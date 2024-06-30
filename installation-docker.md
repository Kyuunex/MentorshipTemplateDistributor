# Installation inside a Docker container
Only recently I started packaging the bot inside a docker container, so, 
these instructions are newly written and not thoroughly tested.

### Requirements: 
+ `git`
+ `docker`

### Intents
[Visit this page](https://discord.com/developers/applications/), locate your bot and enable 
- SERVER MEMBERS INTENT
- MESSAGE CONTENT INTENT

### API keys and tokens
You need to either supply them via environment variables.
| environment variables | where to get |
| ------------- | ------------- |
| MTD_TOKEN  | [create a new app, make a bot acc](https://discord.com/developers/applications/) |

## Docker Compose
The simplest way to run the bot is using the docker-compose (or `docker compose` on newer versions) utility.
In this case, the database will be available outside the container at `/db/data/`

```bash
git clone https://github.com/Kyuunex/MentorshipTemplateDistributor.git -b master MTD  # replace master with version from Releases tab
cd MTD
# make the MTD_TOKEN variable available in your environment, e.g. with a .env or .envrc file
docker-compose up --watch # rebuilds the container if there are changes in /mtd folder

# for older version of docker-compose, after every change:
docker-compose build
docker-compose up
```

## Docker

### Where is the bot's data folder
+ inside the container, `/root/.local/share/MTD`  
If you are restoring a database backup, it goes into this folder.

### Building a docker container
These instructions are newly written and not thoroughly tested, but what you should be doing looks something like this: 

```bash
git clone https://github.com/Kyuunex/MentorshipTemplateDistributor.git -b master MTD # replace master with version from Releases tab
cd MTD
docker build -t mtd .
docker run -e MTD_TOKEN=your_bot_token_goes_here mtd # first run only

docker start container_name # subsequent runs
```

### Updating from inside the container
If you shell into the container, this is how you update the version, you typically shouldn't use docker like this.
```sh
python3 -m pip install git+https://github.com/Kyuunex/MentorshipTemplateDistributor.git@master --upgrade
# wget -O $HOME/.local/share/MTD/maindb.sqlite3 REPLACE_THIS_WITH_DIRECT_FILE_LINK # optional database backup restore
```
replace `master` with version from Releases tab