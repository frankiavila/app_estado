from ldap3 import Server, Connection, SIMPLE, ALL

LDAP_SERVER = 'ldap://srv-sdc.ln.medsol.cu'
LDAP_BASE_DN = 'ou=novatec.users,dc=ln,dc=medsol,dc=cu'
LDAP_DOMAIN = 'ln.medsol.cu'

# Usuario y contraseña de prueba
username = "frank.al"
password = "Irina810424"

user_dn = f"{username}@{LDAP_DOMAIN}"
server = Server(LDAP_SERVER, get_info=ALL)

try:
    conn = Connection(server, user=user_dn, password=password,
                      authentication=SIMPLE, auto_bind=True)

    # Buscar el usuario
    conn.search(
        search_base=LDAP_BASE_DN,
        search_filter=f'(sAMAccountName={username})',
        attributes=['cn', 'memberOf']
    )

    if conn.entries:
        entry = conn.entries[0]
        groups_raw = entry.memberOf.values if 'memberOf' in entry else []
        groups_clean = [g.split(',')[0].replace('CN=', '') for g in groups_raw]

        print("✅ Usuario autenticado:", username)
        print("Grupos del usuario:", groups_clean)
    else:
        print("❌ Usuario no encontrado en LDAP")

    conn.unbind()

except Exception as e:
    print("❌ Error LDAP:", e)
