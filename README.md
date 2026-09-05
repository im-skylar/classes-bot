# classes-bot

## Setup

> If you are on Windows, you may need to replace the `python3` commands with `py`.

0. Create a bot at <https://discord.com/developers/applications> and copy it's login token
1. Create a `.env` file, paste the following and insert your login token and admin role id

```
DISCORD=abcabcabcabc.abcabcabcabcabc-abcabcabc
ADMIN_ROLE=1234123412341234
DB_LOCATION=bot.db
```

2. Run `python3 -m venv venv`
3. Activate the venv `source venv/Scripts/activate` or `source venv/bin/active` (`venv\Scripts\activate.bat` on Windows)
4. To start the bot run `python3 main.py`. This needs to keep running or else the bot will go offline.
   If you're running Linux with Systemd, you can use the provided Systemd Unit file (TODO) by copying `classes-bot.service` to `/etc/systemd/system/`, inserting your user and home path and running `systemctl daemon-reload && systemctl enable classes-bot.service --now`.
5. Use `/change-capacity` in discord to set the capacities of the different schools.

### How to find the admin Role ID
You will either need to create a role for this or use an existing role in your server.

1. Go to _User Settings_ > _Developer_, set _Developer Mode_ to on.
2. Click on a user who has that role and right click on the role. Click _Copy Role ID_


## How to use

Students can choose their preferred school using `/choose-prefs`, preferably giving 2 answers. If they don't they won't get priority next time. If they don't choose anything (or retract their preferences using `/remove-prefs`) they won't get assigned. They can list their current preferences using `/list-prefs`.

Once the application period closes, admins can use `/close-applications` to generate assignments which favor in order: preference, priority, roll. If applicants don't accept their assignment or decline, they will be removed and a space is left for another applicant.

Using `/list-enrollments` a list of all the currently chosen applicants will be outputted.

As of right now, the bot is server-agnostic, meaning that if is added to multiple servers, it will treat them as if it were one big one. Since role IDs are unique, admin actions can only be executed on one server but will effect the state of the bot for all servers (as do any other actions). I strongly recommend running multiple instances for different servers. 

## Todos
- [x] clear enrollments command (or add it to the close appl. command)
- [x] periodically check for open spaces and notify
- [x] maybe an automatic queue for the next applicants
- [x] notify users of their results
- [x] reset aptitude rng to 0-19
- [x] list-applicants not working
- [ ] handle deleted users
- [x] csv export (with priorities listed)
- [x] bug: users without preferences gain priority
- [x] priority reset
- [x] add /change-priority admin command
- [x] reinsert minimum roll
- [ ] bug: handle crash during initial sending
- [x] disallow commands via DM (solution: only disallow commands that need admin privileges, since it's the only time, server info is used)

## Developing Notes
![Status State Machine](./status_statemachine.svg)