# tidbyt-scoreboard
Tidbyt display scoreboard and flask app (proof of concept)

# How to deploy the Flask server

1. Download the Google Cloud SDK
2. Authenticate via `gcloud auth login`
3. Use the following command from within the folder with the dockerfile:

```
gcloud builds submit --tag gcr.io/oddballsportstvdev/be-abc-scoreboard-v1:latest --project=oddballsportstvdev --gcs-log-dir="gs://cf149855-806c-411c-8c51-33d13bd97b7a/builds" ; gcloud run deploy be-abc-scoreboard-v1 --image gcr.io/oddballsportstvdev/be-abc-scoreboard-v1:latest --project=oddballsportstvdev --region us-east4 --platform managed --cpu=1  --memory=1Gi  --min-instances=0
```

NOTE: currently cloud logging isn't working or isn't enabled.  You can ignore the error from the first command and simply view the logs over in Google Cloud Build.

NOTE: there is a semicolon (`;`) separating two commands (`gcloud builds submit` and `gcloud run deploy`)
