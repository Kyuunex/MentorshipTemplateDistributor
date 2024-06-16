async def add_admins(self):
    async with await self.db.execute("SELECT user_id, permissions FROM admins") as cursor:
        admin_list = await cursor.fetchall()

    if not admin_list:
        app_info = await self.application_info()
        if app_info.team:
            for team_member in app_info.team.members:
                await self.db.execute("INSERT INTO admins VALUES (?, ?)", [int(team_member.id), 1])
                print(f"Added {team_member.name} to admin list")
        else:
            await self.db.execute("INSERT INTO admins VALUES (?, ?)", [int(app_info.owner.id), 1])
            print(f"Added {app_info.owner.name} to admin list")
        await self.db.commit()


async def ensure_tables(db):
    await db.execute("""
    CREATE TABLE IF NOT EXISTS "config" (
        "setting"    TEXT, 
        "parent"    TEXT, 
        "value"    TEXT, 
        "flag"    TEXT
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS "admins" (
        "user_id"    INTEGER NOT NULL UNIQUE, 
        "permissions"    INTEGER NOT NULL
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS "ignored_users" (
        "user_id"    INTEGER NOT NULL UNIQUE, 
        "reason"    TEXT
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS "user_extensions" (
        "extension_name"     TEXT
    )
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS "channels" (
        "setting"    TEXT, 
        "guild_id"    INTEGER, 
        "channel_id"    INTEGER
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS "categories" (
        "setting"    TEXT NOT NULL,
        "guild_id"    INTEGER NOT NULL,
        "category_id"    INTEGER NOT NULL
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS "roles" (
        "setting"    TEXT, 
        "guild_id"    INTEGER, 
        "role_id"    INTEGER
    )
    """)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS "guild_event_report_channels" (
        "guild_id"    INTEGER NOT NULL, 
        "channel_id"    INTEGER NOT NULL UNIQUE
    )
    """)

    await db.commit()
