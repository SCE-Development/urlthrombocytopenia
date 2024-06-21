from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, AnyHttpUrl
import logging
from datetime import datetime
import time
import prometheus_client
import uvicorn
from queue import Queue
from threading import Thread
from http import HTTPStatus

from modules.args import get_args
from modules.generate_alias import generate_alias
import modules.sqlite_helpers as sqlite_helpers
from modules.constants import HttpResponse, http_code_to_enum
from modules.metrics import MetricsHandler
from modules.sqlite_helpers import increment_used_column


class CreateRequest(BaseModel):
    """Request schema"""
    url: AnyHttpUrl
    alias: Optional[str] = None
    expiration_epoch: Optional[str] = None


class CreateResponse(BaseModel):
    """Response schema for create request"""
    url: AnyHttpUrl
    alias: str
    created_at: datetime
    expiration_date: Optional[datetime] = None


class ListItem(BaseModel):
    """A single list item in a list response"""
    id: int
    url: AnyHttpUrl
    alias: str
    created_at: datetime
    expiration_date: Optional[datetime] = None
    used: int


class ListResponse(BaseModel):
    """List response for searching for aliases"""
    data: list[ListItem]
    total: int
    rows_per_page: int

app = FastAPI()
args = get_args()
alias_queue = Queue()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

metrics_handler = MetricsHandler.instance()

#maybe create the table if it doesnt already exist
DATABASE_FILE = args.database_file_path
sqlite_helpers.maybe_create_table(DATABASE_FILE)

# middleware to get metrics on HTTP response codes
@app.middleware("http")
async def track_response_codes(request: Request, call_next):
    response = await call_next(request)
    status_code = response.status_code
    MetricsHandler.http_code.labels(request.url.path, status_code).inc()
    return response

@app.post("/create_url")
async def create_url(request: CreateRequest) -> CreateResponse:
    """Create an alias from a URL if the alias is provided it will be used"""
    # Assuming the user input an expiration_date, convert from EPOCH to DATETIME
    if request.expiration_epoch is not None:
        expiration_date = datetime.fromtimestamp(
            request.expiration_epoch).strftime('%Y-%m-%dT%H:%M:%S.%f')
    else:
        expiration_date = None
        
    if request.alias is None:
        if args.disable_random_alias:
            raise HTTPException(HTTPStatus.INVALID_ARGUMENT_EXCEPTION, 
                                detail="alias must be specified")
        else:
            alias = generate_alias(request.url)
    else:
        alias = request.alias

    if not alias.isalnum():
        raise HTTPException(HTTPStatus.INVALID_ARGUMENT_EXCEPTION,
                             detail="alias must only contain alphanumeric characters")

    with MetricsHandler.query_time.labels("create").time():
        timestamp = sqlite_helpers.insert_url(DATABASE_FILE, request.url, alias, expiration_date)
        if timestamp is not None:
            MetricsHandler.url_count.inc(1)
            return CreateResponse(url=request.url, alias=alias, created_at=timestamp, expiration_date=expiration_date)
        else:
            raise HTTPException(status_code=HTTPStatus.CONFLICT)


@app.get("/list")
async def get_urls(search: Optional[str] = None, page: int = 0, sort_by: str = "created_at", order: str = "DESC") -> ListResponse:
    valid_sort_attributes = {"id", "url", "alias", "created_at", "used"}
    if order not in {"DESC", "ASC"}:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Invalid order")
    if sort_by not in valid_sort_attributes:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Invalid sorting attribute")
    if page < 0:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Invalid page number")
    if search and not search.isalnum():
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail=f'search term "{search}" is invalid. only alphanumeric chars are allowed')
    with MetricsHandler.query_time.labels("list").time():
        urls = sqlite_helpers.get_urls(DATABASE_FILE, page, search=search, sort_by=sort_by, order=order)
        total_urls = sqlite_helpers.get_number_of_entries(DATABASE_FILE, search=search)
        response = ListResponse(
            data=list(map(lambda item: ListItem(**item), urls)),
            total=total_urls,
            rows_per_page=sqlite_helpers.ROWS_PER_PAGE)
        return response

@app.get("/find/{alias}")
async def get_url(alias: str):
    logging.debug(f"/find called with alias: {alias}")
    with MetricsHandler.query_time.labels("find").time():
        url_output = sqlite_helpers.get_url(DATABASE_FILE, alias)
        
    if url_output is None:
        raise HTTPException(status_code=HttpResponse.NOT_FOUND.code)
    alias_queue.put(alias)
    return RedirectResponse(url_output)


@app.post("/delete/{alias}")
async def delete_url(alias: str):
    logging.debug(f"/delete called with alias: {alias}")
    with MetricsHandler.query_time.labels("delete").time():
      if(sqlite_helpers.delete_url(DATABASE_FILE, alias)):
          return {"message": "URL deleted successfully"}
      else:
          raise HTTPException(status_code=HttpResponse.NOT_FOUND.code)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    status_code_enum = http_code_to_enum[exc.status_code]
    return HTMLResponse(content=status_code_enum.content, status_code=status_code_enum.code)

@app.get("/metrics")
def get_metrics():
    return Response(
        media_type="text/plain",
        content=prometheus_client.generate_latest(),
    )

logging.Formatter.converter = time.gmtime

logging.basicConfig(
    # in mondo we trust
    format="%(asctime)s.%(msecs)03dZ %(levelname)s:%(name)s:%(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level= logging.ERROR - (args.verbose*10),
)

def consumer():
    while True:
        alias = alias_queue.get()
        if alias is None:  
            break  
        try:
            with MetricsHandler.query_time.labels("increment_used").time():
                increment_used_column(DATABASE_FILE, alias)
        except Exception:
            logging.exception("Error updating used count for alias {alias}")
        finally:
            alias_queue.task_done()


    
# we have a separate __name__ check here due to how FastAPI starts
# a server. the file is first ran (where __name__ == "__main__")
# and then calls `uvicorn.run`. the call to run() reruns the file,
# this time __name__ == "server". the separate __name__ if statement
# is so the thread references the same instance as the global
# metrics_handler referenced by the rest of the file. otherwise,
# the thread interacts with an instance different than the one the
# server uses
if __name__ == "server":
    initial_url_count = sqlite_helpers.get_number_of_entries(DATABASE_FILE)
    MetricsHandler.url_count.inc(initial_url_count)
    consumer_thread = Thread(target=consumer, daemon=True)
    consumer_thread.start()

if __name__ == "__main__":
    logging.info(f"running on {args.host}, listening on port {args.port}")
    uvicorn.run("server:app", host=args.host, port=args.port, reload=True)
