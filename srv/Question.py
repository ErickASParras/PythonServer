#Class to deal with question and all its related activities in a simple way by storing all in a single object
class Question:
    def __init__(self,number,question):
        self.number = number
        self.question = question
        self.awnser = []

    def setAwnser(self,awnser):
        self.awnser.append(awnser)

    def getAwnser(self):
        if len(self.awnser) > 0:
            return self.awnser
        else:
            return ["NOTANSWERED"]
    
    def __str__(self):
        return f"({self.number}) {self.question}"
    
    def toString(self):
        return f"({self.number}) {self.question}"

