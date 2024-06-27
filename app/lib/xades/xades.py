import os
import subprocess
import logging

class Xades(object):
    def sign(self, xml_no_signed_path, xml_signed_path, file_pk12_path, password):
        JAR_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'FirmaElectronica', 'FirmaElectronica.jar')
        JAVA_CMD = 'java'
        
        if not os.path.isfile(JAR_PATH):
            logging.error(f"El archivo JAR no se encontró en la ruta: {JAR_PATH}")
            print(f"El archivo JAR no se encontró en la ruta: {JAR_PATH}")
            return

        try:
            command = [
                JAVA_CMD,
                '-jar',
                JAR_PATH,
                xml_no_signed_path,
                file_pk12_path,
                password,
                xml_signed_path
            ]
            subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            returnCode = e.returncode
            output = e.output
            logging.error('Llamada a proceso JAVA código: %s' % returnCode)
            logging.error('Error: %s' % output)

        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        res = p.communicate()
        return res[0]
