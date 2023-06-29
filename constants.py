import enum

class HttpResponse(enum.Enum):
  
  OK = (200, "success")
  BAD_REQUEST = (400, "<h1>URL Required</h1>")
  NOT_FOUND = (404, "<h1>URL not found</h1>")
  CONFLICT = (409, "<h1>Alias already exists</h1>")
  INTERNAL_SERVER_ERROR = (500, "<h1>Internal server error</h1>")
  def __init__(self, code, content):
    self.code = code
    self.content = content

http_code_to_enum = {
  200: HttpResponse.OK,
  400: HttpResponse.BAD_REQUEST,
  404: HttpResponse.NOT_FOUND,
  409: HttpResponse.CONFLICT,
  500: HttpResponse.INTERNAL_SERVER_ERROR,
}
