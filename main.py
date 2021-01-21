
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands.cooldowns import BucketType
client = commands.Bot(command_prefix='?', help_command=None)
import os
import requests
import random
from keep_running import keep_running
import html

class TriviaBot:

  def __init__(self, difficulty):
    self.difficulty = difficulty
    
    if difficulty == "random":
      self.info = requests.get("https://opentdb.com/api.php?amount=50&type=multiple")
    else: 
      self.info = requests.get("https://opentdb.com/api.php?amount=50{}&type=multiple".format("&difficulty=" + difficulty))
    self.data = self.info.json()      #CONTAINS ALL POSSIBLE DATA.
    self.questions = []               #CONTAINS ALL POSSIBLE QUESTIONS.
    self.q_a = {}                     #MAPS EACH QUESTION TO ITS CORRESPONDING ANSWER
    self.question_index = 0           #INDEX OF THE QUESTION WITHIN THE data FIELD
    self.asking_a_question = False    #BOOLEAN WHICH TRACKS WHEN TO LISTEN FOR ANSWERS
    self.correct_answer = ""          
    self.possible_answers = []        #TRACKS THE FOUR ANSWERS.
    self.numbered_answers = {}        #DICTIONARY WHICH MAPS EACH QUESTIONS NUMBER TO AN ANSWER. 
    
    for result in self.data["results"]:
      self.questions.append(html.unescape(result['question']))
      self.q_a.update({html.unescape(result['question']): html.unescape(result['correct_answer'])})
  
  
#-------------Main Program---------------#

#INITIALISES WITH A NEW trivia_bot OBJECT.
trivia_bot = TriviaBot("random")

# EVENT LISTENER FOR WHEN THE BOT HAS SWITCHED FROM OFFLINE TO ONLINE.
@client.event
async def on_ready():
  print("TriviaBot is here!")


@client.command()
@commands.cooldown(1, 4, commands.BucketType.user)  ##PUTS A 4 SECOND COOLDOWN ON THE COMMAND.
async def trivia(ctx):
  reset_q_a()
  question = get_trivia_question()
  #SENDS THE QUESTION TO DISCORD
  await ctx.channel.send(question)
  #LOOPS THROUGH ALL ANSWERS AND PRINTS EACH ANSWER ON INDIVIDUAL lINES.
  #ALL ANSWERS ARE NUMBERED. 
  for i in range(0, len(trivia_bot.possible_answers)):
    await ctx.channel.send(str(i + 1) + ":  "+ str(trivia_bot.possible_answers[i]))
  #SETS ASKING A QUESTION TO TRUE. THE BOT WILL NOW LOOK FOR MESSAGES THAT MATCH THE ANSWERS.
  trivia_bot.asking_a_question = True


@client.command()
@commands.cooldown(1, 4, commands.BucketType.user)
async def reload(ctx):
  global trivia_bot
  trivia_bot = TriviaBot()
  await ctx.channel.send("Loaded 50 new random trivia questions.")


@client.command()
@commands.cooldown(1, 4, commands.BucketType.user)
async def difficulty(ctx, *args):
  global trivia_bot
  if len(args) == 0:
    await ctx.channel.send("Invalid difficulty. Please use Random, Easy, Medium, or Hard.")
    return
  elif args[0].lower() == "random" or args[0].lower() == "easy" or args[0].lower() == "medium" or args[0].lower() == "hard":
    trivia_bot = TriviaBot(args[0].lower())
    await ctx.channel.send("Difficulty changed to " + args[0].lower().capitalize() + ".")
  else:
    await ctx.channel.send("Invalid difficulty. Please use Random, Easy, Medium, or Hard.")

  
# EVENT LISTENER FOR WHEN A NEW MESSAGE IS SENT TO A CHANNEL.
@client.event
async def on_message(message):
  #IGNORES THE BOTS OWN MESSAGES.
  if message.author == client.user:
    return   
    
  #CHECKS IF USER ENTERED A NUMBER.   
  if trivia_bot.asking_a_question  and message.content.isdigit():
    #CHECKS IF NUMBER IS A 1, 2, 3, or 4. 
    if int(message.content) in range(1,5):
      #CHECKS IF THE NUMBER CORRESPONDS TO THE CORRECT ANSWER.
      if trivia_bot.numbered_answers[int(message.content) - 1] == trivia_bot.correct_answer:
        await message.channel.send("Correct!")
      else:
        await message.channel.send("Incorrect. Answer was: " + str(trivia_bot.correct_answer))
      trivia_bot.asking_a_question = False
  #ALLOWS FOR COMMANDS AND MESSAGES TO BE USED TOGETHER.
  await client.process_commands(message)


"""Resets the question and answer fields."""
def reset_q_a():
  #CHOOSES A NEW RANDOM QUESTION NUMBER
  trivia_bot.question_index = random.randint(0, len(trivia_bot.questions))
  trivia_bot.correct_answer = trivia_bot.q_a[get_trivia_question()]
  #RESETS THE NUMBERED ANSWERS DICTIONARY
  trivia_bot.numbered_answers = {}
  #RESETS LIST OF POSSIBLE ANSWERS
  trivia_bot.possible_answers = get_trivia_answers()
  for i in range(len(get_trivia_answers())):
    #MAPS EACH NUMBER TO A POSSIBLE ANSWER.
    trivia_bot.numbered_answers[i] = trivia_bot.possible_answers[i]
    
  
"""Returns the current question."""  
def get_trivia_question():
  return trivia_bot.questions[trivia_bot.question_index]


"""Returns a shuffled list of possible answers based on the current question number."""
def get_trivia_answers():
  answers = []
  answers.append(html.unescape(trivia_bot.correct_answer))
  for incorrect in trivia_bot.data['results'][trivia_bot.question_index]['incorrect_answers']:
    answers.append(html.unescape(incorrect))
  random.shuffle(answers)
  return answers


"""Returns the list of answers that have been made all lowercase. Useful for ignoring case when answering questions. """
def get_stripped_trivia_answers():
  answers = []
  answers.append(trivia_bot.correct_answer)

  for incorrect in trivia_bot.data['results'][trivia_bot.question_index]['incorrect_answers']:
    answers.append(html.unescape(incorrect))

  #SETS ALL ANSWERS IN THE LIST TO LOWERCASE.
  for i in range(len(answers)):
    stripped_answer = answers[i].lower()
    answers[i] = stripped_answer

  return answers
  

"""Sets trivia_bot's correct answer field based on the current question number."""  
def update_correct_answer():
  trivia_bot.correct_answer = html.unescape(trivia_bot.data['results'][trivia_bot.question_index]['correct_answer'])


#KEEPS THE WEB SERVER RUNNING.
keep_running()    
# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
client.run(os.getenv("TOKEN"))