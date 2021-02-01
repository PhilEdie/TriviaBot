
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from discord.ext.commands.cooldowns import BucketType

client = commands.Bot(command_prefix='?', help_command=None)

import os
import requests
import random
from keep_running import keep_running
import html
import json

class TriviaBot:

  def __init__(self, difficulty):
    self.difficulty = difficulty
    self.info = None                  
    self.data = None                  #CONTAINS ALL POSSIBLE DATA.
    self.questions = []               #CONTAINS ALL POSSIBLE QUESTIONS.
    self.question_to_answer = {}      #MAPS EACH QUESTION TO ITS CORRESPONDING ANSWER
    self.question_index = 0           #INDEX OF THE QUESTION WITHIN THE data FIELD
    self.is_asking_a_question = False    #BOOLEAN WHICH TRACKS WHEN TO LISTEN FOR ANSWERS
    self.correct_answer = ""          #TRACKS THE CURRENT CORRECT ANSWER
    self.possible_answers = []        #TRACKS THE FOUR ANSWERS.
    self.numbered_answers = {}        #DICTIONARY WHICH MAPS EACH QUESTIONS NUMBER TO AN ANSWER. 
    self.get_new_data(self.difficulty)
    

  
  def get_new_data(self, difficulty):
    """
    Requests new data from OpenTDB. Resets fields. Updates questions list and question to answer dictionary.   
    """  
    if difficulty == "random":
      self.info = requests.get("https://opentdb.com/api.php?amount=50&type=multiple")
    else: 
      self.info = requests.get("https://opentdb.com/api.php?amount=50{}&type=multiple".format("&difficulty=" + difficulty))

    self.data = self.info.json()      
    self.questions = []               
    self.question_to_answer = {}      
    self.question_index = 0           
    self.is_asking_a_question = False    
    self.correct_answer = ""          
    self.possible_answers = []        
    self.numbered_answers = {}         
    
    for result in self.data["results"]:
      question = self.decode_html(result['question'])
      correct_answer = self.decode_html(result['correct_answer'])
      self.questions.append(question)
      self.question_to_answer.update({question : correct_answer})

  
  def decode_html(self, html_string):
    """Converts HTML syntax to readable text and returns it."""
    return html.unescape(html_string)

  
  def get_trivia_question(self):
    """Returns the current question."""  
    return self.questions[self.question_index]


  
  def get_difficulty(self):
    """Returns the current difficulty."""
    return self.difficulty

 
  def get_shuffled_trivia_answers(self):
    """Returns a shuffled list of possible answers based on the current question number."""
    answers = []
    answers.append(self.decode_html(self.correct_answer))
    for incorrect in self.data['results'][self.question_index]['incorrect_answers']:
      answers.append(self.decode_html(incorrect))
    random.shuffle(answers)
    return answers


  
  def new_question(self):
    """
    Increases the question index by 1. 
    If the question index is greater than the length of the questions field, loads new data.
    """
    if self.question_index < len(self.questions) -1:
      self.question_index += 1
    else:
      self.get_new_data(self.difficulty)
    self.reset_possible_answers()

  
  def reset_possible_answers(self):
    """Updates the correct_answer, numbered_answers, and possible_answers fields."""
    self.correct_answer = self.question_to_answer[self.get_trivia_question()]
    #RESETS THE NUMBERED ANSWERS DICTIONARY
    self.numbered_answers = {}
    #RESETS LIST OF POSSIBLE ANSWERS
    self.possible_answers = self.get_shuffled_trivia_answers()
    for answer in range(len(self.possible_answers)):
      #MAPS EACH NUMBER TO A POSSIBLE ANSWER.
      self.numbered_answers[answer] = self.possible_answers[answer]



#-------------Main Program---------------#

#INITIALISES WITH A NEW trivia_bot OBJECT.

bot_instances = {}    #DICTIONARY WHICH MAPS GUILD.ID TO TRIVIABOT OBJECT


# EVENT LISTENER FOR WHEN THE BOT HAS SWITCHED FROM OFFLINE TO ONLINE.
@client.event
async def on_ready():
  for guild in client.guilds:
    if guild.id not in bot_instances.keys():
      bot_instances[guild.id] = TriviaBot("random")
      print("Added bot to dictionary: ", str(guild.id))
  print("Bot is ready!")
  

@client.command()
async def help(ctx):
  """Sends the user a private message explaining how to use each of the commands."""

  author = ctx.message.author
  embed = discord.Embed(colour = discord.Colour.orange())
  embed.set_author(name='Help')
  embed.add_field(name='?trivia', value= 'Generates a new trivia question. You can skip a question by calling the trivia command again.', inline=False)
  embed.add_field(name='?difficulty', value= 'Sets the difficulty of the trivia questions. The available difficulties are Easy, Medium, Hard, or Random.', inline=False)

  await author.send(embed=embed)





@client.command()
@commands.cooldown(1, 4, commands.BucketType.channel)  ##PUTS A 4 SECOND COOLDOWN ON THE COMMAND.
async def trivia(ctx):
  """
  Loads a new trivia question. Prints the new question and its possible answers. 
  """

  id = ctx.message.guild.id
  bot = bot_instances[id]

  bot.new_question()
  question = bot.get_trivia_question()
  #SENDS THE QUESTION TO DISCORD
  await ctx.channel.send(question)
  #LOOPS THROUGH ALL ANSWERS AND PRINTS EACH ANSWER ON INDIVIDUAL lINES.
  #ALL ANSWERS ARE NUMBERED. 
  for answer in range(0, len(bot.possible_answers)):
    await ctx.channel.send(str(answer + 1) + ":  "+ str(bot.possible_answers[answer]))
  #SETS ASKING A QUESTION TO TRUE. THE BOT WILL NOW LOOK FOR MESSAGES THAT MATCH THE ANSWERS.
  bot.is_asking_a_question = True




@client.command()
@commands.cooldown(1, 4, commands.BucketType.user)
async def reload(ctx):
  """Creates a new instance of trivia_bot."""
  
  id = ctx.message.guild.id
  bot = bot_instances[id]

  difficulty = bot.get_difficulty()
  bot = TriviaBot(difficulty)
  await ctx.channel.send("Loaded 50 new random trivia questions.")



@client.command()
@commands.cooldown(1, 4, commands.BucketType.user)
async def difficulty(ctx, *args):
  """Creates a new instance of trivia_bot with a specified difficulty."""

  id = ctx.message.guild.id
  bot = bot_instances[id]

  possible_difficulties = ["random", "easy", "medium", "hard"]

  if len(args) == 0:
    await ctx.channel.send("Invalid difficulty. Please use Random, Easy, Medium, or Hard.")
    return

  elif args[0].lower() in possible_difficulties:
    selected_difficulty = args[0].lower()
    bot = TriviaBot(selected_difficulty)
    await ctx.channel.send("Difficulty changed to " + selected_difficulty.capitalize() + ".")

  else:
    await ctx.channel.send("Invalid difficulty. Please use Random, Easy, Medium, or Hard.")

  

@client.event
async def on_message(message):
  """
  Event listener for when a message is sent to a channel. Active when trivia_bot is currently asking a question. 
  """
  #IGNORES THE BOTS OWN MESSAGES.
  if message.author == client.user:
    return
  id = message.guild.id  
  bot = bot_instances[id] 
    
  #CHECKS IF USER ENTERED A NUMBER.   
  if bot.is_asking_a_question  and message.content.isdigit():
    #CHECKS IF NUMBER IS A 1, 2, 3, or 4. 
    if int(message.content) in range(1,5):
      #CHECKS IF THE NUMBER CORRESPONDS TO THE CORRECT ANSWER.
      if bot.numbered_answers[int(message.content) - 1] == bot.correct_answer:
        await message.channel.send("Correct!")
      else:
        await message.channel.send("Incorrect. Answer was: " + str(bot.correct_answer))
      bot.is_asking_a_question = False
  #ALLOWS FOR COMMANDS AND MESSAGES TO BE USED TOGETHER.
  await client.process_commands(message)


#KEEPS THE WEB SERVER RUNNING.
keep_running()    
# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
client.run(os.getenv("TOKEN"))