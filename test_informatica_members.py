from ldap3 import Server, Connection, SIMPLE, ALL

LDAP_SERVER = 'ldap://srv-sdc.ln.medsol.cu'
LDAP_BASE_DN = 'ou=novatec.users,dc=ln,dc=medsol,dc=cu'
LDAP_DOMAIN = 'ln.medsol.cu'

# Usuario y contraseña con permisos para consultar AD
admin_user = "frank.al"
admin_pass = "Irina810424"

user_dn = f"{admin_user}@{LDAP_DOMAIN}"
server = Server(LDAP_SERVER, get_info=ALL)

try:
    conn = Connection(server, user=user_dn, password=admin_pass,
                      authentication=SIMPLE, auto_bind=True)

    # Buscar el grupo 'Informatica'
    conn.search(
        search_base=LDAP_BASE_DN,
        search_filter="(cn=Informatica)",
        attributes=['cn', 'member']
    )

    if conn.entries:
        grupo = conn.entries[0]
        print(f"✅ Grupo encontrado: {grupo.cn.value if 'cn' in grupo else grupo.entry_dn}")
        print("Miembros:")

        for miembro_dn in grupo.member.values:
            # Buscar el objeto miembro por su DN
            conn.search(
                search_base=miembro_dn,
                search_filter="(objectClass=person)",
                attributes=['displayName', 'sAMAccountName']
            )
            if conn.entries:
                entry = conn.entries[0]
                nombre = entry.displayName.value if 'displayName' in entry else miembro_dn
                usuario = entry.sAMAccountName.value if 'sAMAccountName' in entry else None
                print(f"- {nombre} ({usuario})")
    else:
        print("❌ Grupo 'Informatica' no encontrado en LDAP")

    conn.unbind()

except Exception as e:
    print("❌ Error LDAP:", e)
