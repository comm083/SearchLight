import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_cctv_videos():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    print("Checking 'cctv_videos' table...")
    try:
        response = supabase.table('cctv_videos').select('*').limit(3).execute()
        data = response.data
        if data:
            for i, row in enumerate(data):
                print(f"[{i}] ID: {row.get('id')}")
                print(f"    Filename: {row.get('video_filename')}")
                print(f"    Date: {row.get('event_date')}")
                print(f"    Summary: {row.get('summary')}")
                print(f"    Frames: {row.get('frames')}")
                print("-" * 20)
        else:
            print("No data found in 'cctv_videos'.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_cctv_videos()
