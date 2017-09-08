import aq

class Record:

    def __init__(self,model,data):
        self.model = model
        self.__data = data
        self.__has_one_models = {}
        for key in data:
            setattr(self,key,data[key])

    def has_one(self,name,model):
        self.__has_one_models[name] = model
        # print(self.__data)
        if name in self.__data:
            # print("Setting up association with existing data from " + name)
            setattr(self,name,model.record(self.__data[name]))

    def get_one(self,name,model):
        reference = name + "_id"
        result = model.find(getattr(self,reference))
        setattr(self,name,result)
        return result

    def __getattr__(self, name):

        # print("method missing for " + name)

        def __get_one_wrapper(name,model):
            return self.get_one(name,model)

        if name in self.__has_one_models:
            return __get_one_wrapper(name,self.__has_one_models[name])
        else:
            raise Exception("Method " + name + " not found.")
