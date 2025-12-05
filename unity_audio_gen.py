import os
import argparse
import json
import glob
import soundfile as sf
# We assume the script is running from F:\GithubProjects\kokoro\
from kokoro import KPipeline

def generate_audio(text, output_path, voice_code, pipeline):
    if not text: return
    
    # print(f"    Processing: {voice_code}...")
    try:
        # Generate audio
        generator = pipeline(text, voice=voice_code, speed=1.0, split_pattern=r'\n+')
        for i, (graphemes, phonemes, audio) in enumerate(generator):
            sf.write(output_path, audio, 24000)
            break 
    except Exception as e:
        print(f"    [Error] {voice_code} failed: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_file", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--lang", type=str, default="a")
    
    # We add this just so the C# script doesn't crash if it sends --mode
    # It doesn't actually do anything, but it prevents errors.
    parser.add_argument("--mode", type=str, default="batch") 

    args = parser.parse_args()

    # 1. AUTO-DETECT AVAILABLE VOICES
    # Looks for .pt files in the 'voices' folder next to this script
    voices_dir = os.path.join(os.path.dirname(__file__), "voices")
    voice_files = glob.glob(os.path.join(voices_dir, "*.pt"))
    
    # Convert file paths to voice codes (e.g., "voices/af_heart.pt" -> "af_heart")
    available_voices = [os.path.splitext(os.path.basename(f))[0] for f in voice_files]

    if not available_voices:
        print("Error: No voice models found in 'voices' folder!")
        return

    print(f"Found {len(available_voices)} voices: {available_voices}")

    # 2. LOAD PIPELINE
    print("Loading Model...")
    pipeline = KPipeline(lang_code=args.lang) 

    # 3. READ JSON
    if not os.path.exists(args.json_file):
        print(f"Error: JSON file not found at {args.json_file}")
        return

    with open(args.json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Processing {len(data)} words across {len(available_voices)} voices...")

    # 4. MAIN LOOP
    for word_id, content in data.items():
        print(f"Generating Word: '{word_id}'")
        
        # Parse text (handles both simple string or object format)
        text_to_speak = ""
        if isinstance(content, str):
            text_to_speak = content
        elif isinstance(content, dict):
            text_to_speak = content.get("text", "")

        # Create Folder for this WORD
        # Result: Assets/Audio/Words/hero_attack_01/
        word_folder = os.path.join(args.output_dir, word_id)
        if not os.path.exists(word_folder):
            os.makedirs(word_folder)

        # Generate for ALL voices
        for voice in available_voices:
            filename = f"{voice}.wav"
            full_path = os.path.join(word_folder, filename)
            
            # --- ADD THIS CHECK ---
            if os.path.exists(full_path):
                print(f"Skipping {voice} (Already exists)")
                continue
            # ----------------------

            generate_audio(text_to_speak, full_path, voice, pipeline)
    print("Done!")

if __name__ == "__main__":
    main()