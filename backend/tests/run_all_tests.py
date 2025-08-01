#!/usr/bin/env python3
"""
Test runner principal que ejecuta todos los tests.
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def run_all_tests():
    """Ejecuta todos los tests del proyecto."""
    try:
        print("🚀 Iniciando ejecución de todos los tests...")
        
        # Obtener el directorio de tests
        tests_dir = Path(__file__).parent
        
        # Tests a ejecutar
        test_files = [
            "agents/test_langchain_system.py",
            "services/test_chat_service.py", 
            "routers/test_travel_router.py"
        ]
        
        results = []
        
        for test_file in test_files:
            test_path = tests_dir / test_file
            if test_path.exists():
                print(f"\n📋 Ejecutando: {test_file}")
                try:
                    # Ejecutar el test
                    result = subprocess.run([
                        sys.executable, str(test_path)
                    ], capture_output=True, text=True, cwd=tests_dir.parent)
                    
                    if result.returncode == 0:
                        print(f"✅ {test_file} - PASÓ")
                        results.append((test_file, True, result.stdout))
                    else:
                        print(f"❌ {test_file} - FALLÓ")
                        print(f"Error: {result.stderr}")
                        results.append((test_file, False, result.stderr))
                        
                except Exception as e:
                    print(f"❌ {test_file} - ERROR: {e}")
                    results.append((test_file, False, str(e)))
            else:
                print(f"⚠️ {test_file} - NO ENCONTRADO")
        
        # Resumen final
        print("\n" + "="*50)
        print("📊 RESUMEN DE TESTS")
        print("="*50)
        
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        for test_file, success, output in results:
            status = "✅ PASÓ" if success else "❌ FALLÓ"
            print(f"{status} - {test_file}")
        
        print(f"\n🎯 RESULTADO: {passed}/{total} tests pasaron")
        
        if passed == total:
            print("🎉 ¡TODOS LOS TESTS PASARON!")
        else:
            print("⚠️ Algunos tests fallaron")
            
    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 