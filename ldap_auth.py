from ldap3 import Server, Connection, SIMPLE, ALL
from typing import Optional, List
import logging

# Configuración del servidor LDAP
LDAP_SERVER = 'ldap://srv-sdc.ln.medsol.cu'
LDAP_BASE_DN = 'ou=novatec.users,dc=ln,dc=medsol,dc=cu'
LDAP_DOMAIN = 'ln.medsol.cu'


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Autentica al usuario contra AD y valida que esté en el grupo 'Informatica'.
    """
    user_dn = f"{username}@{LDAP_DOMAIN}"
    server = Server(LDAP_SERVER, get_info=ALL)

    try:
        logging.info(f"🔑 Intentando bind con DN={user_dn}")
        conn = Connection(server, user=user_dn, password=password,
                          authentication=SIMPLE, auto_bind=True)
        logging.info("✅ Conexión LDAP establecida")

        # Buscar el usuario por su sAMAccountName
        conn.search(
            search_base=LDAP_BASE_DN,
            search_filter=f'(sAMAccountName={username})',
            attributes=['cn', 'memberOf']
        )
        logging.info(f"📂 Resultado búsqueda usuario: {conn.entries}")

        if conn.entries:
            entry = conn.entries[0]
            groups_raw = entry.memberOf.values if 'memberOf' in entry else []
            groups_clean = [g.split(',')[0].replace('CN=', '') for g in groups_raw]

            logging.info(f"👤 Usuario {username} pertenece a los grupos: {groups_clean}")

            # Validar que esté en el grupo Informatica
            if "Informatica" not in groups_clean:
                conn.unbind()
                logging.warning("⚠️ Usuario no pertenece al grupo Informatica")
                return None

            conn.unbind()
            return {"username": username, "groups": groups_clean}

        conn.unbind()

    except Exception as e:
        logging.error(f"❌ Error LDAP: {e}")

    return None


def get_informatica_members(admin_user: str, admin_pass: str) -> List[dict]:
    """
    Devuelve únicamente los miembros del grupo 'Informatica'.
    """
    user_dn = f"{admin_user}@{LDAP_DOMAIN}"
    server = Server(LDAP_SERVER, get_info=ALL)

    miembros = []
    try:
        logging.info(f"🔑 Conectando como {user_dn} para obtener miembros del grupo Informatica")
        conn = Connection(server, user=user_dn, password=admin_pass,
                          authentication=SIMPLE, auto_bind=True)
        logging.info("✅ Conexión LDAP establecida para miembros")

        # Buscar solo el grupo 'Informatica'
        conn.search(
            search_base=LDAP_BASE_DN,
            search_filter="(cn=Informatica)",
            attributes=['member']
        )
        logging.info(f"📂 Resultado búsqueda grupo Informatica: {conn.entries}")

        if conn.entries:
            for miembro_dn in conn.entries[0].member.values:
                conn.search(
                    search_base=miembro_dn,
                    search_filter="(objectClass=person)",
                    attributes=['displayName', 'sAMAccountName']
                )
                if conn.entries:
                    entry = conn.entries[0]
                    nombre = entry.displayName.value if 'displayName' in entry else miembro_dn
                    usuario = entry.sAMAccountName.value if 'sAMAccountName' in entry else None
                    miembros.append({
                        "nombre": nombre,
                        "username": usuario
                    })
                    logging.info(f"👥 Miembro encontrado: {nombre} ({usuario})")

        conn.unbind()

    except Exception as e:
        logging.error(f"❌ Error LDAP al obtener miembros: {e}")

    return miembros
