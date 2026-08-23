# classes-bot

## setup

1. Create a `.env` file, paste the following and insert your api key and admin role id

```
DISCORD=abcabcabcabc.abcabcabcabcabc-abcabcabc
ADMIN_ROLE=1234123412341234
DB_LOCATION=bot.db
```

## how to use

Students can choose their preferred school using `/choose-prefs`, preferably giving 2 answers. If they don't they won't get priority next time. If they don't choose anything (or retract their preferences using `/remove-prefs`) they won't get assigned. They can list their current preferences using `/list-prefs`.

Once the application period closes, admins can use `/close-applications` to generate assignments which favor in order: preference, priority, roll. If applicants don't accept their assignment [TODO!], they will be removed and a space is left for another applicant.

Using `/list-enrollments` a list of all the currently chosen applicants will be outputted. Currently this mentions everyone on that list.



## todos
- [x] clear enrollments command (or add it to the close appl. command)
- [x] periodically check for open spaces and notify
- [x] maybe an automatic queue for the next applicants
- [x] notify users of their results
- [ ] reset aptitude rng to 0-19
- [x] list-applicants not working
