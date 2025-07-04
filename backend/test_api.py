"""
Script de test pour vérifier le fonctionnement de FastAPI
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI(title='Test API')


@app.get('/')
async def root():
    return {'message': 'API de test fonctionne!'}


if __name__ == '__main__':
    uvicorn.run('test_api:app', host='0.0.0.0', port=8000, reload=True)
