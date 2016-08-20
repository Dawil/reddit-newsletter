# Reddit Newsletter

Reddit takes a bunch of news articles and used crowd sourced curation to create a ranking of most significant articles to least, at any gien time. This is useful on a busy news day as I know which articles to apy attention to, and which not to. On a slow news day, however, reddit still presents the same number of articles, even though nothing is happening.

Reddit should not be about occupying my time, but about notifying me when, and only when, there is something occuring that I should know about.

Hence reddit newsletter. For each subreddit, or signal, that I'm subscribed to, reddit newsletter will calculate a standard deviation of article rankings, then only show me articles above a chosen percentile threshold. That way on slow days I'll receive little and on busy days I'll remain up to date.

### Shouldn't Reddit do this?

Reddit receives money from ads, so it's in their interest to always have something for you when you visit their site. So Unless reddit changes their business model it seems unlikely they'll want to offer this.

## Architecture

### Data Storage

To keep things simple I'll use a filesystem database. However I could see myself changing this to something more proper with a real database, so I'll create a Data layer, making any potential move in the future easier.

### Data Capture

Reddit can present its pages in JSON format. I can parse a subreddit's JSON data to get the information I need.

### Workflow

For now I'll make this a manually run script, probably run once daily, that'll then email all new significant articles to me.


# USAGE

```
$ python main.py --directory data --email dave@davidgwilcox.com update_subreddits
$ python main.py --directory data --email dave@davidgwilcox.com send_new_articles
```
