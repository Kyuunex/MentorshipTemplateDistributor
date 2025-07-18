# Mentorship Template Distributor
This is just a Discord bot that automates the speedmapping contest in the osu! Mentorship Discord server, to some extent.

## Contest Setup
- Set the server where all participants are in `!set_representing_server 205772326678167552`
- Set Cycle ID `!set_cycle_id 26`
- Set late submission rule: `!set_late_submission 1` 
  - Set 0 for no and 1 for yes.
- Set contest start time (UTC): `!set_start 2024-06-22 00:00:00`
  - Or Set contest start time (UNIX): `!set_start_unix 1719014400`
- Set contest end time (UTC): `!set_end 2024-06-23 23:59:59`
  - Or Set contest end time (UNIX): `!set_end_unix 1719187199`
- Set duration (in minutes): `!set_duration osu 180` `!set_duration taiko 120` `!set_duration mania 150` `!set_duration ctb 240`
  - Gamemode exact keywords: `osu`, `taiko`, `mania`, `ctb`
- Make user ineligible to participate (formers who are judges, etc): `!add_ineligible osu 346755297714372609`
  - Gamemode exact keywords: `osu`, `taiko`, `mania`, `ctb`
- Add eligible roles: `!add_eligible_role osu 335116624019324928`
  - Gamemode exact keywords: `osu`, `taiko`, `mania`, `ctb`
  - I went ahead and grabbed all the Role IDs from the mentorship server:
    ```
    !add_eligible_role osu 335116624019324928
    !add_eligible_role osu 335117782343614464
    !add_eligible_role taiko 373570114525724682
    !add_eligible_role taiko 401866034769821696
    !add_eligible_role mania 401865892205559809
    !add_eligible_role mania 401865885280894977
    !add_eligible_role ctb 335116700338880532
    !add_eligible_role ctb 335117832041791498
    ```
    - Note that few former mentees are judges and can not participate, so this eligibility test will work in combination with the previous command.
- Set Attachment: `!set_attachment https://blabla`
- Set Instructions: `!set_instructions Here is the beatmap template for the Speedmapping Contest. After you are done, use the !submit command, attach a file and send it to this bot. Since we are using a bot, anything could go wrong, so send a copy to Dignan as well just to be safe. Good luck!`

## DM monitoring (Code stolen from Momiji lol)
- Message a member `!message_member`
- Read member replies `!read_dm_reply`
- Mirror member DMs to a channel: `!set_dm_mirror_channel` (run in a channel you want to mirror to)

## Participant facing commands
- Check eligibility `!check_eligibility`
- Request participation: `!participate osu`
  - Gamemode exact keywords: `osu`, `std`, `taiko`, `mania`, `ctb`, `catch`, `fruits`
  - Added more keywords to the user facing side but in the DB, these will be replaced with the keywords mentioned earlier.
- Submit entry: `!submit` MUST attach a .osu file to the message

## Contest Tools
- Export participant data: `!export_participants`
  - result:
    ```json
    [
      {
        "cycle_id": 26,
        "user_id": 155976140073205761,
        "username": "kyuunex",
        "nickname": "Kyuunex",
        "gamemode": "osu",
        "timestamp_requested": 1719014400,
        "timestamp_submitted": 1719024400,
        "timestamp_timeslot_deadline": 1719025200,
        "timestamp_grace_deadline": 1719025500,
        "status": "VALID"
      }
    ]
    ```
    - status: DNS - did not submit, LATE - deadline exceeded, VALID - A valid entry.
- Reset participant: `!reset_participant discord_id`. In case something breaks, they get another go.
- Export submissions (in a zip download): `!export_submissions`
