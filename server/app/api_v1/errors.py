from . import api 




@api.app_errorhandler(404)
def not_found(error):
    return {"error": "Resource not found"}, 404     

@api.app_errorhandler(400)
def bad_request(error):         
    return {"error": "Bad request"}, 400

@api.app_errorhandler(500)
def internal_server_error(error):
    return {"error": "Internal server error"}, 500  

@api.app_errorhandler(401)
def unauthorized(error):
    return {"error": "Unauthorized"}, 401   

@api.app_errorhandler(403)
def forbidden(error):
    return {"error": "Forbidden"}, 403  

@api.app_errorhandler(409)
def conflict(error):
    return {"error": "Conflict"}, 409

@api.app_errorhandler(422)
def unprocessable_entity(error):
    return {"error": "Unprocessable entity"}, 422

@api.app_errorhandler(429)
def too_many_requests(error):
    return {"error": "Too many requests"}, 429  

@api.app_errorhandler(503)
def service_unavailable(error):
    return {"error": "Service unavailable"}, 503    

@api.app_errorhandler(504) 
def gateway_timeout(error):
    return {"error": "Gateway timeout"}, 504

@api.app_errorhandler(505)
def http_version_not_supported(error):
    return {"error": "HTTP version not supported"}, 505 
