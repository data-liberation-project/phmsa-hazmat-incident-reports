import json
import logging
import re
import time
import typing
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from retry import retry

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CLIENT_STATE_XML = open("data/manual/dashboard-state.xml").read()
CLIENT_QUERY_XML = open("data/manual/query-template.xml").read()
QUERY_FIELDS = re.findall(r"\{(.*)\}", CLIENT_QUERY_XML)

BASE_URL = "https://portal.phmsa.dot.gov/analytics/saw.dll"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:68.0) Gecko/20100101 Firefox/68.0",  # noqa: E501
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/x-www-form-urlencoded",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://portal.phmsa.dot.gov/phmsapub/PHMSALoginForm.html",
    "Connection": "keep-alive",
    "Keep-Alive": "timeout=5, max=100",
}


class MissingState(Exception):
    pass


class ViewStateMissing(MissingState):
    pass


class CSXMissing(MissingState):
    pass


def extract_state(res: requests.Response) -> tuple[str, str]:
    content = res.content.decode("utf-8")
    content = re.sub(r"\\u003c", "<", content)

    pat = r'"viewState":"([^"]+)"'
    match = re.search(pat, content)

    if match is None:
        raise ViewStateMissing("Cannot find ViewState on page")

    view_state = match.group(1)

    pat = r"<sawst:envState xmlns.*?</sawst:envState>"
    match = re.search(pat, content)

    if match is None:
        raise CSXMissing("Cannot find client state XML on page")

    csx: str = json.loads(f'["{match.group(0)}"]')[0]

    return view_state, csx


class Session:
    def __init__(self, debug: bool = False) -> None:
        self._session = requests.Session()

        self.debug = debug
        if debug:
            self.created_at = datetime.now().isoformat().replace(":", "-")
            self.debug_dir = Path(f"debug/{self.created_at}/")
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            self.debug_req_i = 0

    def req(
        self,
        name: str,
        method: typing.Callable[..., requests.Response],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> requests.Response:
        res = method(*args, **kwargs)

        if self.debug:
            debug_path = self.debug_dir / f"{self.debug_req_i:03d}-{name}.html"
            with open(debug_path, "wb") as f:
                f.write(res.content)
            self.debug_req_i += 1

        return res

    @retry(tries=5, delay=5, backoff=2, logger=logger)
    def get(
        self, name: str, *args: typing.Any, **kwargs: typing.Any
    ) -> requests.Response:
        return self.req(name, self._session.get, *args, **kwargs)

    @retry(tries=5, delay=5, backoff=2, logger=logger)
    def post(
        self, name: str, *args: typing.Any, **kwargs: typing.Any
    ) -> requests.Response:
        return self.req(name, self._session.post, *args, **kwargs)

    def initialize(self) -> None:
        logger.debug("Initializing ...")

        portal_url = f"{BASE_URL}?Portalpages&PortalPath=%2Fshared%2FPublic%20Website%20Pages%2F_portal%2FHazmat%20Incident%20Report%20Search"  # noqa: E501

        init_url = f"https://portal.phmsa.dot.gov/PDMPublicReport/?url={portal_url}"

        HEADERS["Original-Request"] = init_url

        auth_url = "https://portal.phmsa.dot.gov/PDMPublicReport/auth2/oam/server/auth_cred_submit"  # noqa: E501

        self.get("init", init_url)
        self.get("portal", portal_url, headers=HEADERS, allow_redirects=True)
        self.post(
            "auth",
            auth_url,
            data="---------------------------------------------------------",
            headers=HEADERS,
        )
        self.get("portal", portal_url, headers=HEADERS, allow_redirects=True)

    def compose_query(self, **params: str) -> str:
        query_xml = CLIENT_QUERY_XML
        for field in QUERY_FIELDS:
            val = params[field.lower()]
            query_xml = query_xml.replace(f"{{{field}}}", val)
        return query_xml

    def query(self, **params: str) -> tuple[str, dict[str, str]]:
        """
        `params` are the templating values available
        in data/manual/query-template.xml.

        This method returns a "ClientStateXml" string
        necessary for specifying the download.
        """
        logger.debug("Querying ...")
        query_xml = self.compose_query(**params)
        data = dict(
            ViewState="7m3hnikntaqp81992oti7ajp52",
            ClientStateXml=CLIENT_STATE_XML,
            fmapId="noDEvw",
            reloadTargets="all",
            Page="Hazmat Incident Report",
            IgnoreBypassCacheOption="ignoreBypassCache",
            PageDelayedState="NotDelayed",
            PortalPath="/shared/Public Website Pages/_portal/Hazmat Incident Report Search",  # noqa: E501
            Action="ApplyFilter",
            ViewID="d:dashboard~p:kav0ge6phc5j2g2v~s:57jkpieh0769ioam~g:33ptcjsu3i8hrgkl",  # noqa: E501
            StateAction="samePageState",
            P0=query_xml,
            P1="dashboard",
            Caller="PortalPages",
            _scid="",
            icharset="utf-8",
        )
        data_str = "&".join(f"{key}={quote(val)}" for key, val in data.items())

        res = self.post(
            "query",
            BASE_URL + "?ReloadDashboard",
            data=data_str,
            headers=HEADERS,
        )

        view_state, csx = extract_state(res)

        download_params = dict(
            ViewID="d:dashboard~p:kav0ge6phc5j2g2v~r:1hn2ls7a7d2j3j0e",
            Action="Download",
            Style="Skyros",
            ItemName="Incident Report All fields included in Form 5800",
            path="/shared/Public Website Pages/HAZMAT Incidents/Incident Report All fields included in Form 5800",  # noqa: E501
            Format="csv",
            Extension=".csv",
            bNotSaveCommand="true",
            clientStateXml=csx,
            _scid="",
        )

        return view_state, download_params

    def expand_results(self, view_state: str) -> tuple[str, dict[str, str]]:
        logger.debug("Expanding to full set of columns ...")

        data = dict(
            Path="/shared/Public Website Pages/HAZMAT Incidents/Incident Detailed Report: All fields included in Form 5800",  # noqa: E501
            Action="promptstart",
            style="PHMSA",
            Options="r",
            ViewState=view_state,
            StateAction="samePageState",
            ViewID="d:dashboard~p:kav0ge6phc5j2g2v~r:trg1arf44ggobm05",
            Done="Close",
            _scid="",
        )

        data_str = "&".join(f"{key}={quote(val)}" for key, val in data.items())

        res = self.post(
            "expand",
            BASE_URL + "?Go",
            data=data_str,
            headers=HEADERS,
        )

        view_state, csx = extract_state(res)

        download_params = dict(
            ViewID="d:dashboard~p:kav0ge6phc5j2g2v~r:trg1arf44ggobm05",
            Action="Download",
            Style="Skyros",
            Options="rd",
            ViewState=view_state,
            ItemName="Incident Report All fields included in Form 5800",
            path="/shared/Public Website Pages/HAZMAT Incidents/Incident Report All fields included in Form 5800",  # noqa: E501
            Format="csv",
            Extension=".csv",
            bNotSaveCommand="true",
            clientStateXml=csx,
            _scid="",
        )

        return view_state, download_params

    def download_set_guard(self, download_id: int) -> None:
        self.post(
            "download-guard",
            BASE_URL + "?DownloadGuard",
            data=f"DownloadId={download_id}&_scid=&icharset=utf-8",
        )

    def download_start(self, download_id: int, download_params: dict[str, str]) -> None:
        logger.debug("Requesting download ...")
        data = {**download_params, **dict(DownloadId=str(download_id))}

        data_str = "&".join(f"{key}={quote(val)}" for key, val in data.items())

        self.post(
            "download-start",
            BASE_URL + "?Go",
            data=data_str,
        )

    def download_check_is_ready(self, download_id: int) -> bool:
        res = self.post(
            "download-status",
            BASE_URL + "?DownloadStatus",
            data=f"DownloadId={download_id}&Action=GetStatus&_scid=&icharset=utf-8",
        )

        content = res.content.decode("utf-8")
        match = re.search('status="(.*?)"', content)
        if match is None:
            raise ValueError("Cannot find status in response")

        status = match.group(1)
        logger.debug(f"Download status: {status}")
        return status == "done"

    def download(self, download_params: dict[str, str]) -> bytes:
        download_id = int(time.time() * 1000)

        self.download_set_guard(download_id)
        self.download_check_is_ready(download_id)
        self.download_start(download_id, download_params)

        while True:
            if self.download_check_is_ready(download_id):
                break
            time.sleep(0.5)

        res = self.get(
            "download_file", f"{BASE_URL}?downloadExportedFile&DownloadId={download_id}"
        )

        return res.content


def fetch(expand: bool = False, **params: str) -> bytes:
    session = Session()
    session.initialize()

    view_state, download_params = session.query(**params)
    if expand:
        view_state, download_params = session.expand_results(view_state)

    file_bytes = session.download(download_params)
    return file_bytes
