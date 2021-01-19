
import discord
import os
import requests
import random
from keep_running import keep_running
import time
import html

class TriviaBot:

  def __init__(self):
    #INITIALISE FIELDS
    
    self.info = requests.get("https://opentdb.com/api.php?amount=50&difficulty=medium&type=multiple")
    self.data = self.info.json()      #CONTAINS ALL POSSIBLE DATA.
    self.questions = []               #CONTAINS ALL POSSIBLE QUESTIONS.
    self.q_a = {}                     #MAPS EACH QUESTION TO ITS CORRESPONDING ANSWER
    self.question_index = 0           #INDEX OF THE QUESTION WITHIN THE data FIELD
    self.asking_a_question = False    #BOOLEAN WHICH TRACKS WHEN TO LISTEN FOR ANSWERS
    self.correct_answer = ""          
    self.possible_answers = []        #TRACKS THE FOUR ANSWERS.
    self.numbered_answers = {}        #DICTIONARY WHICH MAPS EACH QUESTIONS NUMBER TO AN ANSWER.
    self.last_command = time.time()   #COOLDOWN TIMER WHICH PREVENTS USERS FROM SPAMMING COMMANDS INTO DISCORD. 
    
    for result in self.data["results"]:
      self.questions.append(html.unescape(result['question']))
      self.q_a.update({html.unescape(result['question']): html.unescape(result['correct_answer'])})
 
#-------------Main Program---------------#

client = discord.Client()
trivia_bot = TriviaBot()


# EVENT LISTENER FOR WHEN THE BOT HAS SWITCHED FROM OFFLINE TO ONLINE.
@client.event
async def on_ready():
  print("TriviaBot is here!")
  

# EVENT LISTENER FOR WHEN A NEW MESSAGE IS SENT TO A CHANNEL.
@client.event
async def on_message(message):
  
  #IGNORES THE BOTS OWN MESSAGES.
  if message.author == client.user:
    return

  #IF IT HAS BEEN 5 SECONDS SINCE THE LAST COMMAND AND ?trivia IS CALLED:
  if time.time() - trivia_bot.last_command > 5 and message.content == "?trivia":
      reset_q_a()
      question = get_trivia_question()
      #SENDS THE QUESTION TO DISCORD
      await message.channel.send(question)
      #LOOPS THROUGH ALL ANSWERS AND PRINTS EACH ANSWER ON INDIVIDUAL lINES.
      #ALL ANSWERS ARE NUMBERED. 
      for i in range(0, len(trivia_bot.possible_answers)):
        await message.channel.send(str(i + 1) + ":  "+ str(trivia_bot.possible_answers[i]))
      #SETS ASKING A QUESTION TO TRUE. THE BOT WILL NOW LOOK FOR MESSAGES THAT MATCH THE ANSWERS.
      trivia_bot.asking_a_question = True
      #RESETS THE COOLDOWN TIMER. 
      trivia_bot.last_command = time.time()
    
  #CHECKS ANSWER. IGNORING CASE.
  if trivia_bot.asking_a_question and message.content.lower() in get_stripped_trivia_answers():
    if message.content.lower() == trivia_bot.correct_answer.lower():
      await message.channel.send("Correct!")
    else:
      await message.channel.send("Incorrect. Answer was: " + str(trivia_bot.correct_answer))
    #NOW LISTENS TO ?trivia
    trivia_bot.asking_a_question = False
    
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