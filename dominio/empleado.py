from dominio.rut import validar_rut
from dominio.persona import Persona
from dominio.cuentaUsuario import CuentaUsuario
from validaciones import validar_fecha, validar_salario, validar_rol, validar_id_opcional


class Empleado(Persona):
    def __init__(self, id_empleado, nombre, direccion, telefono,
                 correo, fecha_inicio, salario, rol="Empleado", rut=None):
        super().__init__(nombre, direccion, telefono, correo)
        self._id_empleado = validar_id_opcional(id_empleado)
        self._fecha_inicio = validar_fecha(fecha_inicio)
        self.set_salario(salario)
        self._rol = validar_rol(rol)
        self.__cuenta_usuario = None
        self._rut = None if rut is None else validar_rut(rut)

    def get_rut(self):
        return self._rut

    def get_id(self):
        return self._id_empleado

    def get_fecha_inicio(self):
        return self._fecha_inicio

    def get_rol(self):
        return self._rol

    def get_salario(self):
        return self.__salario

    def set_salario(self, salario):
        self.__salario = validar_salario(salario)

    def asignar_cuenta(self, cuenta):
        if not isinstance(cuenta, CuentaUsuario):
            raise TypeError("Debe asignar un objeto de la clase CuentaUsuario.")
        if cuenta.get_correo() != self.get_correo():
            raise ValueError("La cuenta debe usar el correo del empleado.")
        self.__cuenta_usuario = cuenta

    def get_cuenta_usuario(self):
        return self.__cuenta_usuario

    def mostrar_datos(self):
        return (
            "ID: {} | Nombre: {} | Direccion: {} | Telefono: {} | "
            "Correo: {} | Inicio: {} | Salario: {:.2f} | Rol: {} | RUT: {}"
        ).format(
            self._id_empleado, self._nombre, self._direccion, self._telefono,
            self._correo, self._fecha_inicio, self.__salario, self._rol, self._rut
        )
