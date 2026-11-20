# Cómo exportar informes en EcoTech

El gerente puede consultar el informe general en la consola o guardarlo en Excel y PDF. Cada vez que se elige una de estas opciones, EcoTech lee los datos actuales de empleados, proyectos, departamentos y tiempo de trabajo desde Supabase.

## Pasos para exportar

1. Abre la carpeta del proyecto en VS Code. Si es la primera ejecución en ese computador, completa la instalación y configuración descritas en el [README](README.md).
2. Desde la terminal de PowerShell, inicia EcoTech:

   ```powershell
   .\.venv\Scripts\python.exe main.py
   ```

3. En **ECOTECH - ACCESO**, elige **1. Iniciar sesión** e ingresa con una cuenta de **gerente**.
4. En el menú del gerente, selecciona la opción que necesites:

   | Opción | Acción | Resultado |
   |---:|---|---|
   | 15 | Generar informes de Supabase | Muestra el informe general en la consola. |
   | 16 | Guardar informe en Excel | Genera un archivo `.xlsx` con cuatro hojas. |
   | 17 | Guardar informe en PDF | Genera un archivo `.pdf` con las cuatro secciones y las páginas numeradas. |

5. Si elegiste **16** o **17**, la consola muestra **«Informe guardado en:»** seguido de la ruta completa. Puedes generar ambos formatos seleccionando primero una opción y luego la otra.

## Contenido del informe

| Sección | Datos incluidos |
|---|---|
| Empleados | ID, nombre, dirección, teléfono, correo, inicio de contrato, salario y rol. |
| Proyectos | ID, nombre, descripción, fecha de inicio, miembro y presupuesto. |
| Departamentos | ID, nombre, descripción, ID del gerente y nombre del gerente. |
| Tiempo | ID del registro, fecha, empleado, proyecto, horas trabajadas y tareas realizadas. Al final aparece el total de horas. |

Si una sección está vacía, aparece **«Sin registros»**. El informe se puede generar aunque todavía no haya datos en todas las secciones. En Excel, cada sección ocupa una hoja. En PDF, cada sección comienza en una página nueva.

## Dónde se guardan los archivos

En la primera exportación se crea la carpeta `reportes/` dentro del proyecto. Cada archivo lleva la fecha y la hora de generación. Ejemplos de nombres:

```text
reportes/informe_ecotech_2026-11-19_10-30-00_123456.xlsx
reportes/informe_ecotech_2026-11-19_10-31-12_654321.pdf
```

Las exportaciones anteriores se conservan. La carpeta `reportes/` está excluida de Git porque los informes pueden contener datos personales y salarios.

## Si tienes un problema

- **Solo ves las opciones de datos personales, horas, clima y dólar.** Estás en el menú del empleado. Cierra la sesión e ingresa con una cuenta de gerente para exportar.
- **Falta una biblioteca.** Desde la carpeta del proyecto, ejecuta `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. La exportación usa `openpyxl` para Excel y `reportlab` para PDF.
- **El archivo no aparece donde lo buscabas.** Revisa la ruta completa que imprimió la consola. Si se informó un error al guardar, comprueba que tengas permiso de escritura en la carpeta del proyecto.
- **Falló la conexión a Supabase.** Restablece la conexión y vuelve a generar el informe. La exportación consulta la base de datos de la empresa; los respaldos locales corresponden a las consultas de dólar y clima.

## Código de la exportación

`crear_informe_desde_supabase()`, en `presentacion/menu.py`, consulta los registros y construye el objeto `Informes`. La clase está en `dominio/informe.py`: `obtener_secciones()` organiza las filas, `calcular_total_horas()` suma las horas y `exportar_excel()` o `exportar_pdf()` genera el archivo correspondiente.