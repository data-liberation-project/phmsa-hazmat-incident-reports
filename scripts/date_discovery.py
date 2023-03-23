import csv
import git
import io
import os
import re

from argparse import ArgumentParser
from datetime import timezone
from glob import glob

DATA_PATH = 'data/fetched'
OUT_PATH = 'data/processed'
RE_PATTERN = '<a href = .*>(.*)</A>$'
BACKUP_RE_PATTERN = '[A-Z]+-[0-9]+'

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--data_path',default=DATA_PATH)
    parser.add_argument('--out_path',default=OUT_PATH)
    parser.add_argument('--re_pattern',default=RE_PATTERN)
    return parser.parse_args()

def get_paths(root_dir,data_path,out_path):
    fetched_data_path = os.path.join(root_dir, data_path)
    out_data_path = os.path.join(root_dir, out_path)
    os.makedirs(fetched_data_path,exist_ok=True)
    os.makedirs(out_data_path,exist_ok=True)
    return fetched_data_path, out_data_path

def parse_report_number(report_number_str,pattern=RE_PATTERN,backup_pattern=BACKUP_RE_PATTERN):
    if re.match(pattern, report_number_str):
        return re.search(pattern, report_number_str)[1]
    elif re.match(backup_pattern, report_number_str):
        return re.search(backup_pattern, report_number_str)[0]
    else:
        print(f'could not parse from {report_number_str}')
        return None
    
def write_dd_csv(csv_filename,date_dict):
    with open(csv_filename,'w',newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['report number','file','commit','date'])
        for k, v in date_dict.items():
            writer.writerow([k,v['file'],v['commit'],v['dt']])

def discover_dates(repo,fetched_data_path,re_pattern):
    discovered_dates = {}
    for file_name in glob(os.path.join(fetched_data_path,'*.csv')):
        file_basename = os.path.basename(file_name)
        commits = list(reversed(list(repo.iter_commits("main",paths=[os.path.join(fetched_data_path,file_basename)]))))
        for commit in commits:
            dt = commit.committed_datetime.astimezone(timezone.utc)
            blob = [l for l in commit.tree.traverse() if isinstance(l, git.Blob) and l.name == file_basename]
            if len(blob) < 1:
                print(f'could not find {file_basename} blob in commit {commit.hexsha}')
            else:
                data_stream = io.StringIO(blob[0].data_stream.read().decode("utf-8-sig"))
                data = csv.DictReader(data_stream,delimiter=',',quotechar='"',quoting=csv.QUOTE_ALL,skipinitialspace=True)
                for row in data:
                    report_number = parse_report_number(row['Report Number'],pattern=re_pattern)
                    if report_number not in discovered_dates:
                        discovered_dates[report_number] = {
                            'file': file_basename,
                            'commit': commit.hexsha,
                            'dt': dt,
                        }
    return discovered_dates

def main():
    args = parse_args()
    repo = git.Repo(os.getcwd(), search_parent_directories=True)
    root_dir = repo.git.rev_parse("--show-toplevel")
    fetched_data_path, out_data_path = get_paths(root_dir, args.data_path, args.out_path)
    discovered_dates = discover_dates(repo, fetched_data_path, args.re_pattern)
    write_dd_csv(os.path.join(out_data_path,'discovered_dates.csv'),discovered_dates)

if __name__ == "__main__":
    main()