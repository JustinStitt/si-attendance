This is done _automagically_ by vercel on my account.

If you are forking this repo you need to setup vercel yourself:

To do that, make a `vercel.json` file as shown below:
```
{
    "version": 2,
    "builds": [
        {
            "src": "./index.py",
            "use": "@vercel/python"
        }
    ],
    "routes": [
        {
            "src": "/(.*)",
            "dest": "/"
        }
    ]
}
```


Reference: https://dev.to/andrewbaisden/how-to-deploy-a-python-flask-app-to-vercel-2o5k
