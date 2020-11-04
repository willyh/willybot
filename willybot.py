import speech_recognition as sr

# Value between 0 and 1 (inclusive).
# Lower this if willybot is hearing too few words
STRICTNESS = 0.99

def any_in(words, sentence):
    return len(words) == 0 or True in map(lambda w: w in sentence, words)

def all_in(words, sentence):
    return len(words) == 0 or not False in map(lambda w: w in sentence, words)

def wait_command(sufficient, necessary, extra=[]):
    r = sr.Recognizer()
    words = ""
    keywords = list(map(lambda w: (w, STRICTNESS), sufficient + necessary + extra))
    while not (any_in(sufficient, words) and all_in(necessary, words)):
        with sr.Microphone() as source:
            try:
                audio = r.listen(source, phrase_time_limit=4)
                words = r.recognize_sphinx(audio, keyword_entries=keywords)
                print(words)
            except sr.UnknownValueError:
                print("No recognizable speech :(")
            except sr.RequestError:
                print("Please run: pip3 install pocketsphinx")

# application specific functions
def lights_command_given(sock, audio_buf, RATE, SAMPLE_WIDTH):
    r = sr.Recognizer()
    audio = sr.AudioData(audio_buf, RATE, SAMPLE_WIDTH)
    all_words = ["willy", "daddy", "bought", "light", "lights", "please", "turn"]
    ke = list(map(lambda w: (w, STRICTNESS), all_words))
    try:
        sentence = r.recognize_sphinx(audio, keyword_entries=ke)
        print(sentence)
        willybot = ["willy", "bought", "light"]
        willydaddy = ["willy", "daddy", "light"]
        return all_in(willybot, sentence) or all_in(willydaddy, sentence)
    except sr.UnknownValueError:
        print("No recognizable speech :(")
        return False
    except sr.RequestError:
        print("Please run: pip3 install pocketsphinx")
        return False

def wait_lights_command():
    wait_command([], ["willy", "bought", "light"], ["turn", "please", "on", "off"])
