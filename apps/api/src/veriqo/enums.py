from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    TECHNICIAN = "technician"
    VIEWER = "viewer"
    CUSTOMER = "customer"
