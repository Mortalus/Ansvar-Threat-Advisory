#!/usr/bin/env python3
"""
Final test of the optimized threat refinement system
"""
import requests
import time

def test_optimized_system():
    print('Testing optimized refinement after full restart...')
    
    # Wait for API
    for i in range(5):
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print(f'✓ API ready after {i+1} attempts')
                break
        except:
            print(f'Waiting for API... attempt {i+1}')
            time.sleep(3)
    else:
        print('❌ API not ready')
        return False
    
    # Create a very simple test
    print('\nCreating simple test pipeline...')
    try:
        # Simple upload
        test_doc = 'Web Server connects to Database'
        files = {'files': ('simple.txt', test_doc, 'text/plain')}
        response = requests.post('http://localhost:8000/api/documents/upload', files=files, timeout=20)
        
        if response.status_code != 200:
            print(f'❌ Upload failed: {response.status_code}')
            return False
        
        pipeline_id = response.json().get('pipeline_id')
        print(f'✓ Pipeline created: {pipeline_id}')
        
        # Quick DFD
        response = requests.post('http://localhost:8000/api/documents/extract-dfd', 
                               json={'pipeline_id': pipeline_id}, timeout=20)
        if response.status_code != 200:
            print(f'❌ DFD failed: {response.status_code}')
            return False
        print('✓ DFD extracted')
        
        # Review
        dfd_data = response.json()
        response = requests.post('http://localhost:8000/api/documents/review-dfd',
                               json={'pipeline_id': pipeline_id, 'dfd_components': dfd_data['dfd_components']}, timeout=20)
        if response.status_code != 200:
            print(f'❌ DFD review failed: {response.status_code}')
            return False
        print('✓ DFD reviewed')
        
        # Generate threats (this step might be slow)
        print('Generating threats (may take time)...')
        start = time.time()
        response = requests.post('http://localhost:8000/api/documents/generate-threats',
                               json={'pipeline_id': pipeline_id}, timeout=120)
        
        if response.status_code != 200:
            print(f'❌ Threat generation failed: {response.status_code}')
            print(response.text[:200])
            return False
        
        print(f'✓ Threats generated in {time.time() - start:.1f}s')
        threats = response.json().get('threats', [])
        print(f'  Generated {len(threats)} threats')
        
        # Test optimized refinement
        print('\nTesting OPTIMIZED refinement...')
        start = time.time()
        response = requests.post('http://localhost:8000/api/documents/refine-threats',
                               json={'pipeline_id': pipeline_id}, timeout=30)
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('refinement_stats', {})
            method = stats.get('refinement_method', 'unknown')
            
            print(f'✅ OPTIMIZED refinement successful in {elapsed:.1f}s!')
            print(f'  Method: {method}')
            print(f'  Threats: {stats.get("original_count", 0)} -> {stats.get("final_count", 0)}')
            
            refined_threats = data.get('refined_threats', [])
            if refined_threats:
                sample = refined_threats[0]
                print(f'\nSample refined threat:')
                print(f'  Name: {sample.get("Threat Name", "N/A")}')
                print(f'  Risk Score: {sample.get("risk_score", "N/A")}')
                print(f'  Priority: {sample.get("implementation_priority", "N/A")}')
                print(f'  Business Risk: {sample.get("business_risk_statement", "N/A")[:80]}...')
            
            if method == 'optimized_batch':
                print('\n🎉 Successfully using OPTIMIZED refiner!')
                return True
            else:
                print('\n⚠️  Still using old refiner')
                return False
                
        else:
            print(f'❌ Refinement failed: {response.status_code}')
            print(response.text[:300])
            return False
    
    except Exception as e:
        print(f'❌ Test failed: {e}')
        return False

if __name__ == "__main__":
    success = test_optimized_system()
    print(f"\n{'✅ SUCCESS!' if success else '❌ FAILED'}")
    exit(0 if success else 1)