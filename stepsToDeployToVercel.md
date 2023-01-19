make venv
make restful flask api
pip freeze to requirements.txt

make a vercel.json file as shown below:
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
vercel (follow CLI setup)
done ?!

https://dev.to/andrewbaisden/how-to-deploy-a-python-flask-app-to-vercel-2o5k
