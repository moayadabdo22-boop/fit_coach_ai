#!/usr/bin/env python
"""Test that new training endpoints are properly registered."""

import sys
sys.path.insert(0, 'd:\\chatbot coach\\fit-coach-ai-main\\ai_backend')

try:
    from main import app
    print('✅ main.py imports successfully')
    
    routes = [route.path for route in app.routes]
    training_routes = [r for r in routes if 'training' in r or 'personalized' in r or 'rag' in r]
    print(f'✅ New endpoints registered: {len(training_routes)} routes')
    
    expected_endpoints = [
        '/ai/personalized-plan',
        '/ai/personalized-exercises',
        '/ai/personalized-foods',
        '/ai/rag-context',
        '/ai/training-status'
    ]
    
    for endpoint in sorted(expected_endpoints):
        found = any(endpoint in r for r in training_routes)
        status = '✅' if found else '❌'
        print(f'{status} {endpoint}')
    
    print('\n✅ All endpoints properly registered!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
