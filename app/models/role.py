from enum import Enum


class RoleEnum(str, Enum):
    REPORTANTE = "reportante"
    TECNICO = "tecnico"
    RESPONSABLE_AREA = "responsable_area"
    COORDINADOR = "coordinador"
    ADMINISTRADOR = "administrador"
    VALIDADOR = "validador"
