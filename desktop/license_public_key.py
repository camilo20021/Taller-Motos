# Clave PÚBLICA Ed25519 usada para validar los archivos de licencia (.lic).
#
# Esta clave es segura de distribuir con la aplicación: solo sirve para
# VERIFICAR firmas, no para crearlas. La clave PRIVADA correspondiente vive
# únicamente en tools/private_key.pem, en la máquina del vendedor, y nunca
# se sube al repositorio (ver .gitignore).
#
# Si alguna vez se necesita rotar el par de claves, hay que regenerar ambas
# a la vez y volver a compilar la aplicación con la nueva clave pública.

PUBLIC_KEY_B64 = "NFbnJhFc94QF0Zrqyq/SxwKKnpHF8DrmEWAN5gH0oCE="
