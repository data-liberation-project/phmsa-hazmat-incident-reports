import csv
import git
import io
import os
import re
from datetime import timezone
from glob import glob

def parse_report_number(report_number_str, pattern='^<a href = .*>(.*)</A>$'):
    groups = re.search(pattern, report_number_str)
    if groups:
        return groups[1]
    else:
        print(f'could not parse from {report_number_str}')
        return None
    
def write_dd_csv(csv_filename,date_dict):
    with open(csv_filename,'w',newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['report number','file','commit','date'])
        for k, v in date_dict.items():
            writer.writerow([k,v['file'],v['commit'],v['dt']])

def main():
    repo = git.Repo(os.getcwd())
    fetched_data_path = os.path.join(os.getcwd(), 'data', 'fetched')
    discovered_dates = {}
    for file_name in glob(os.path.join(fetched_data_path,'*.csv')):
        file_basename = os.path.basename(file_name)
        commits = list(reversed(list(repo.iter_commits("main",paths=[os.path.join(fetched_data_path,file_basename)]))))
        for commit in commits:
            dt = commit.committed_datetime.astimezone(timezone.utc)
            blob = [l for l in commit.tree.traverse() if isinstance(l, git.Blob) and l.name == file_basename]
            if len(blob) < 1:
                print(blob)
            else:
                data_stream = io.StringIO(blob[0].data_stream.read().decode("utf-8-sig"))
                data = csv.DictReader(data_stream,delimiter=',',quotechar='"',quoting=csv.QUOTE_ALL,skipinitialspace=True)
                for row in data:
                    report_number = parse_report_number(row['Report Number'])
                    if report_number not in discovered_dates:
                        discovered_dates[report_number] = {
                            'file': file_basename,
                            'commit': commit.hexsha,
                            'dt': dt,
                        }
    write_dd_csv('discovered_dates.csv',discovered_dates)

if __name__ == "__main__":
    main()