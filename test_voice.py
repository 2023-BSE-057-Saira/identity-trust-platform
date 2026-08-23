from app.modules.voice_auth.voice_analysis import match_speakers, detect_voice_spoof

print("Speaker match:", match_speakers("voice_ref.wav", "voice_test.wav"))
print("Spoof check (ref):", detect_voice_spoof("voice_ref.wav"))
print("Impostor check:", match_speakers("voice_ref.wav", "voice_impostor.wav"))