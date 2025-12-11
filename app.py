from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)

# UPDATE THIS PATH to where your Excel file is located
DATA_FILE = '/Users/opheliachen/Downloads/GTA_Tennis_clubs_data_.xlsx'

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (pd.Int64Dtype, pd.Int32Dtype)):
            return int(obj)
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

def load_data():
    """Load both sheets from Excel"""
    df_all = pd.read_excel(DATA_FILE, sheet_name='data')
    df_processed = pd.read_excel(DATA_FILE, sheet_name='run')
    return df_all, df_processed

def get_stats(df_all, df_processed):
    """Calculate statistics"""
    total = int(len(df_all))
    processed = int(len(df_processed))
    remaining = total - processed
    
    # Check all 9 required fields
    required_fields = [
        'Location', 'Email', 'Club Type', 'Membership Status', 
        'Waitlist Length', 'Number of Courts', 'Court Surface', 'Operating Season'
    ]
    
    completeness = {}
    for col in required_fields:
        if col in df_processed.columns:
            not_found = int(df_processed[col].astype(str).str.contains('Not Found', case=False, na=False).sum())
            null_count = int(df_processed[col].isnull().sum())
            complete = processed - not_found - null_count
            completeness[col] = {
                'complete': int(complete),
                'total': int(processed),
                'percentage': round((complete / processed * 100) if processed > 0 else 0, 1)
            }
    
    return {
        'total': total,
        'processed': processed,
        'remaining': remaining,
        'completion_rate': round((processed / total * 100) if total > 0 else 0, 1),
        'completeness': completeness
    }

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    try:
        df_all, df_processed = load_data()
        stats = get_stats(df_all, df_processed)
        return jsonify(stats)
    except Exception as e:
        print(f"Error in /api/stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/processed')
def api_processed():
    try:
        _, df_processed = load_data()
        clubs = df_processed.fillna('N/A').to_dict('records')
        return jsonify(clubs)
    except Exception as e:
        print(f"Error in /api/processed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/remaining')
def api_remaining():
    try:
        df_all, df_processed = load_data()
        processed_names = set(df_processed['Club Name'].str.strip().str.lower())
        remaining = df_all[~df_all['Club Name'].str.strip().str.lower().isin(processed_names)]
        clubs = remaining.to_dict('records')
        return jsonify(clubs)
    except Exception as e:
        print(f"Error in /api/remaining: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape/start', methods=['POST'])
def api_scrape_start():
    try:
        data = request.json
        batch_size = data.get('batch_size', 10)
        
        df_all, df_processed = load_data()
        processed_names = set(df_processed['Club Name'].str.strip().str.lower())
        remaining = df_all[~df_all['Club Name'].str.strip().str.lower().isin(processed_names)]
        
        batch = remaining.head(batch_size)
        
        return jsonify({
            'status': 'ready',
            'batch_size': len(batch),
            'total_remaining': len(remaining),
            'clubs': batch[['Club Name', 'Website URL']].to_dict('records')
        })
    except Exception as e:
        print(f"Error in /api/scrape/start: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export')
def api_export():
    try:
        _, df_processed = load_data()
        output_path = '/tmp/tennis_clubs_export.csv'
        df_processed.to_csv(output_path, index=False)
        return send_file(output_path, as_attachment=True, download_name='gta_tennis_clubs.csv')
    except Exception as e:
        print(f"Error in /api/export: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎾 GTA TENNIS CLUBS DASHBOARD - CHAMPIONSHIP EDITION")
    print("="*60)
    print("\n📊 Required Data Fields (9 total):")
    print("   1. Club Name")
    print("   2. Location")
    print("   3. Email")
    print("   4. Club Type")
    print("   5. Membership Status")
    print("   6. Current Waitlist Length")
    print("   7. Number of Courts")
    print("   8. Court Surface")
    print("   9. Operating Season")
    print("\n🌐 Access dashboard at: http://localhost:5001")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
