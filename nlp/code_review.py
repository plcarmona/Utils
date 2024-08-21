import os, io, pstats
from pstats import SortKey
import cProfile
import anthropic
from dotenv import load_dotenv
import mdprint
load_dotenv()
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

model="claude-3-haiku-20240307"
def profile(func):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE  # 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        with open('profile_output.txt', 'w+') as f:
            f.write(s.getvalue())
        return retval
    
    return wrapper


def code_review(file_path):

    with open(file_path, "r") as file:
        code = file.read()

    #if exist delete output.txt
    if os.path.exists("profile_output.txt"):
        os.remove("profile_output.txt")

    #create function that eval script
    @profile
    def eval_code(code):
        exec(code)
        return code

    eval_code(code)
    
    with open("profile_output.txt", "r") as f:
        profile_info = f.read()

    return profile_info, code



def prompt_maker(profile, code):
    prompt = f"""
    Here is the code:
    <Code>{code}</Code>

    Here is the profile information:
    <Profile>{profile}</Profile>

"""
    return prompt

def review_file(path,model ="claude-3-haiku-20240307",output="response.md"):

    profile,code = code_review(path)
    prompt = prompt_maker(profile, code)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system = "You are a senior developer at a tech company. You are reviewing a code snippet from a junior developer. The code snippet is below. Please provide feedback on the code snippet. Create a layout of the code in md resume the profile and add suggestions for improvement.",
        messages=[{"role": "user", "content": f"{prompt}"}]
    )
    content = response.content[0]

    md = content.model_dump()["text"]
    mdprint.mdprint(md)

    with open(output, 'w') as f:
        f.write(md)


