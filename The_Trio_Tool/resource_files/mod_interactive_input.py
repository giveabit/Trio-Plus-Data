def main():
    pass

if __name__ == '__main__':
    main()
    """not meant to be called from outside"""
    foo=input('this module is meant to be called from within another program <enter>')



def ask (question = '', defaultAnswer = '', valid_answers='', typeOfQuestion = 1, regEx =''):
    """
    interactive user input routine with check for valid answer.

    Question types are

    1: Yes/No - returns 1/0
    2: integer digit value
    3: float digit value (will accept , and .)
    4: RegEx - returns string
    5: valid string only - returns one of the valid answers
    6: valid integer only - returns one of the valid answers
    7: arbitrary - accepts everything
    """

    while True:
        answer = input(''+question+' [%s]: ' % defaultAnswer)
        answer = answer or defaultAnswer

        if typeOfQuestion == 1: # yes/no type
            if answer.lower() in ['n', 'no']:
                return 0
            elif answer.lower() in ['y', 'yes']:
                return 1
            else:
                print ('y/n or yes/no')

        if typeOfQuestion == 2: # integer type
            try:
                return int(answer)
            except:
                print('integer digit input only')


        if typeOfQuestion == 3: # float type
            try:
                return float(answer.replace(',','.')) # comma handling here
            except:
                print('float input only')

        if typeOfQuestion == 4: # RegEx type
            import re
            p = re.compile(regEx)
            m = p.match(answer)
            if m:
                return m.group()
            else:
                print('\ninput format error!\nthe RegEx expected was:\n'+regEx)

        if typeOfQuestion == 5 :# valid string answers only
            if answer in valid_answers:
                return answer.rstrip()

        if typeOfQuestion == 6 :# valid integer answers only
            try:
                if int(answer) in valid_answers:
                    return int(answer)
            except:
                pass


        if typeOfQuestion == 7: # arbitrary
            return answer




