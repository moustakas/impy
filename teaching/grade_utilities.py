################################################################################
import numpy as np

# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
################################################################################


################################################################################
def calc_average_of_grades(grades, drop_lowest_score=False):
    scores = []
    #print grades
    for g in grades:
        score = g.grade_pct()
        scores.append(score)

    if drop_lowest_score is True:
        scores.sort()
        scores.reverse()
        scores.pop()

    #print scores
    return 100*np.mean(scores)

################################################################################
def is_lowest_grade(list_of_grades, grade):

    all_scores = []
    for g in list_of_grades:
        all_scores.append(g.grade_pct())

    ret = False
    all_scores.sort()
    if grade.grade_pct() == all_scores[0]:
        ret = True

    return ret 

################################################################################

################################################################################
class Grade_file_info:
    def __init__(self, grade_type):
        self.grade_type = grade_type
        self.date = ''
        self.grade_index = -1
        self.internal_index = -1
        self.max_grade = 100.0
        self.add_index = -1
        self.subtract_index = -1
        self.add = 0.0
        self.subtract = 0.0

    def set_date(self, date):
        self.date = date

    def set_grade_index(self, grade_index):
        self.grade_index = grade_index

    def set_internal_index(self, internal_index):
        self.internal_index = internal_index

    def set_max_grade(self, max_grade):
        self.max_grade = max_grade

    def set_add_index(self, add_index):
        self.add_index = add_index

    def set_subtract_index(self, subtract_index):
        self.subtract_index = subtract_index

    def set_add(self, add):
        self.add = add

    def set_subtract(self, subtract):
        self.subtract = subtract


################################################################################

################################################################################
class Grade:
    def __init__(self, grade_type, internal_index, score, max_score, added, subtracted, late, date):
        self.grade_type = grade_type
        self.internal_index = internal_index
        self.score = score
        self.max_score = max_score
        self.added = added
        self.subtracted = subtracted
        self.late = late
        self.date = date

    def grade_sum(self):
        ret = self.score + self.added
        if self.late:
            ret -= self.subtracted
        return ret

    def grade_pct(self):
        ret = self.grade_sum()/self.max_score
        return ret

    def summary_output(self):
        ret = "%5.1f   -   %5.1f" % (100.0*self.grade_pct(),self.score)
        if self.late:
            ret += " (an additional -%4.1f for being late)" % (self.subtracted)
        ret += " out of a possible %5.1f" % (self.max_score)
        return ret
################################################################################
class Course_grades:
    def __init__(self):
        self.quizzes = []
        self.hw = []
        self.exams = []
        self.exam1 = []
        self.exam2 = []
        self.final_exam = []

    def add_grade(self, grade, grade_type):
        
        if grade_type=='quiz' or grade_type=='Quiz' or grade_type=='Q' or grade_type=='q':
            self.quizzes.append(grade)
        elif grade_type=='HW' or grade_type=='hw' or grade_type=='homework' or grade_type=='Homework':
            self.hw.append(grade)
        elif grade_type=='exam' or grade_type=='Exam':
            self.exams.append(grade)
        elif grade_type=='final_exam' or grade_type=='Finalexam' or grade_type=='finalexam' or grade_type=='FinalExam':
            self.final_exam.append(grade)

################################################################################
class Student:
    def __init__(self, student_name, grades, email=None):
        self.student_name = student_name
        self.email = email
        self.grades = grades

    def summary_output(self,final_grade_weighting=[0.2,0.2,0.2,0.2,0.2],summarize=False):

        averages = [-1, -1, -1, -1]
        ret = "-----------------------------------\n"
        ret += "%s %s\n" % (self.student_name[1], self.student_name[0])

        # Quizzes
        ret += " -----\nQuizzes\n -----\n"
        #drop_lowest_score = True
        drop_lowest_score = False
        picked_a_lowest = False
        for g in self.grades.quizzes:
            #ret +=  "%-7s %2s (%10s) %s" % (g.grade_type,g.internal_index,g.date,g.summary_output())
            ret +=  "%-7s (%10s) %s" % (g.grade_type,g.date,g.summary_output())
            if drop_lowest_score==True:
                if is_lowest_grade(self.grades.quizzes,g) and not picked_a_lowest:
                    ret += "\tlowest score, will not be counted in average."
                    picked_a_lowest = True
            ret += "\n"
        avg = calc_average_of_grades(self.grades.quizzes, drop_lowest_score)
        averages[0] = avg
        ret += "\tQuiz avg: %4.2f\n" % (avg)

        # HW
        #drop_lowest_score = True
        drop_lowest_score = False
        picked_a_lowest = False
        ret += " -----\nHomeworks\n -----\n"
        for g in self.grades.hw:
            #ret +=  "%-7s   %2s (%10s) %s" % (g.grade_type,g.internal_index,g.date,g.summary_output())
            ret +=  "%-7s (%10s) %s" % (g.grade_type,g.date,g.summary_output())
            if drop_lowest_score==True:
                if is_lowest_grade(self.grades.hw,g) and not picked_a_lowest:
                    ret += "\tlowest score, will not be counted in average."
                    picked_a_lowest = True
            ret += "\n"
        avg = calc_average_of_grades(self.grades.hw, drop_lowest_score)
        averages[1] = avg
        ret += "\tHW   avg: %4.2f\n" % (avg)

        # Exam 1 
        #drop_lowest_score = True
        drop_lowest_score = False
        picked_a_lowest = False
        ret += " -----\nExams\n -----\n"
        #print len(self.grades.exams)
        if len(self.grades.exams)<=1:
            drop_lowest_score = False
        for g in self.grades.exams:
            ret +=  "%-7s (%10s) %s" % (g.grade_type,g.date,g.summary_output())
            if drop_lowest_score==True:
                #print g.grade_pct()
                #print is_lowest_grade(self.grades.exams,g)
                if is_lowest_grade(self.grades.exams,g) and not picked_a_lowest:
                    ret += "\tlowest score, will not be counted in average."
                    picked_a_lowest = True
            ret += "\n"
        avg = calc_average_of_grades(self.grades.exams, drop_lowest_score)
        averages[2] = avg
        ret += "\tExams avg: %4.2f\n" % (avg)

        '''
        # Exam 2 
        drop_lowest_score = False
        #ret += " -----\nExam 2\n -----\n"
        for g in self.grades.exam2:
            #ret +=  "%-7s   %2s (%10s) %s\n" % (g.grade_type,g.internal_index,g.date,g.summary_output())
            1
        avg = calc_average_of_grades(self.grades.exam2, drop_lowest_score)
        averages[3] = avg
        ret += "\tExam 2  : %4.2f\n" % (avg)
        '''

        # Final Exam 
        drop_lowest_score = False
        ret += " -----\nFinal exam\n -----\n"
        for g in self.grades.final_exam:
            ret +=  "%-7s (%10s) %s" % (g.grade_type,g.date,g.summary_output())
            #1
            #ret +=  "%-7s   %2s (%10s) %s\n" % (g.grade_type,g.internal_index,g.date,g.summary_output())
        if len(self.grades.final_exam)>=1:
            avg = calc_average_of_grades(self.grades.final_exam, drop_lowest_score)
            averages[3] = avg
        else:
            averages[3] = averages[2] # Set final exam grade equal to exam grade so far.
            avg = averages[3]

        ret += "\tFinal exam  : %4.2f\n" % (avg)

        tot = 0.0
        tot_wt = 0.0
        for g,w in zip(averages,final_grade_weighting):
            if g>=0:
                tot += g*w
                tot_wt += w
        final = tot/tot_wt
        ret += "\n -------\n\tFinal grade: %4.2f\n" % (final)

        averages.append(final)

        return averages, ret


    ############################################################################
    def gvis_output(self,final_grade_weighting=[0.2,0.2,0.2,0.2,0.2]):

        averages = [-1, -1, -1, -1, -1]
        drop_lowest_score = True
        picked_a_lowest = False
        ret = ""
        for g in self.grades.quizzes:
            ret += "[\'%s %s\', " % (self.student_name[1], self.student_name[0])
            ret += "new Date(%s,%d,%s)," % (g.date.split('/')[2], int(g.date.split('/')[0])-1, g.date.split('/')[1])
            if drop_lowest_score==True:
                if is_lowest_grade(self.grades.quizzes,g) and not picked_a_lowest:
                    picked_a_lowest = True
            avg = calc_average_of_grades(self.grades.quizzes, drop_lowest_score)
            averages[0] = avg
            ret += "%3.2f],\n" % (avg)


        return ret



################################################################################
def email_grade_summaries(email_address,msg_from,msg_subject,msg_body,password="xxx"):

    ################################################################################
    # Use my GMail account
    ################################################################################
    smtpserver = 'smtp.gmail.com'
    #smtpuser = 'matthew.bellis@gmail.com'  # for SMTP AUTH, set SMTP username here
    smtpuser = msg_from  # for SMTP AUTH, set SMTP username here
    smtppasswd = password  # for SMTP AUTH, set SMTP password here
    #me = 'matthew.bellis@gmail.com'
    me = msg_from

    # Create a text/plain message
    msg = MIMEText(msg_body)
    msg['Subject'] = '%s' % (msg_subject)
    msg['From'] = me
    msg['To'] = email_address

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    try:
        session = smtplib.SMTP('smtp.gmail.com',587)
        session.starttls()
        session.login(smtpuser,smtppasswd)
        session.sendmail(me, email_address, msg.as_string())
        print "Successfully sent email"
        session.quit()
    except smtplib.SMTPException:
        print "Error: unable to send email"




