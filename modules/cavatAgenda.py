# agenda implementation for closure

class agenda():

    def __init__(self):
        self.ag = {}
        self.k = set()
    
    def __str__(self):
        outstring = 'size=' + str(self.len()) + ': '
        keys = self.keys()
        for key in keys:
            v = self.val(key[0], key[1])
            outstring += ' '.join((key[0], v, key[1])) + ';  '
        return outstring
    
    def keys(self):
        return frozenset(self.k)
    
    def pop(self):
        # like dictionary.popitem() - return a random (arg, arg, value) tuple and remove it from the agenda
        
        if self.empty():
            return None
        
        (a,b) = self.k.pop()
        v = self.ag[a][b]
        
        del self.ag[a][b]
        if not len(self.ag[a]):
            del self.ag[a]
        
        return (a, b, v)
    
    def val(self, arg1, arg2):
        # look up a value
        # calling func can behave itself or deal with its own exceptions, what am I, it's mummy? plus, not checking for exceptions gets us a 10% speed increase
        return self.ag[arg1][arg2]
    
    def set(self, arg1, arg2, val):
        # assert a value, but don't overwrite
        
        self.k.add((arg1, arg2))

        if arg1 not in self.ag:
            self.ag[arg1] = {}

        if arg2 in self.ag[arg1]:
            return
        
        self.ag[arg1][arg2] = val

    def len(self):
        return len(self.k)
    
    def empty(self):
        # returns True if has more than 0 entries
        return (len(self.k) == 0)
