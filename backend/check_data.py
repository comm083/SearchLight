from app.services.database import db_service
resp = db_service.supabase.table('cctv_vectors').select('id, content, metadata').order('id').limit(5).execute()
for r in resp.data:
    print(f"ID={r['id']} | location={r['metadata'].get('location','')} | content={r['content'][:100]}")
