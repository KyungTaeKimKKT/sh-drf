


class Serializer_m2m:
    """ m2m filed는 'fks_json', 'fks_files', 'fks_ids' 세 구분으로 나뉘어서 handling"""
    def _update_validated_data(self, instance, validated_data) :
        # validated_data['첨부파일수'] = instance.file_fks.count()
        return validated_data
    
    def _instance_fk_file_manage(self, instance):
        if hasattr(self, 'fk_file'):
            fk_file = getattr(self, 'fk_file')     
                   
            for key, Model in fk_file.items():
                if getattr(self, key) is None: continue
                if hasattr(self, key):
                    fk_name = key.replace('_file', '')
                    setattr(instance, fk_name, Model.objects.create(file=getattr(self, key)))
                    instance.save()


    def _instanace_fks_manage(self, instance, fks_json:dict=None, fks_files:dict=None , fks_ids:dict=None) ->None:
        """
            fks_json = { str : Model }, str은 fks attribute Name
        """
        if fks_json is None :
            fks_json = getattr(self, "fks_json") if hasattr(self, "fks_json") else {}
                
        if fks_files is None :
            fks_files = getattr(self, "fks_files") if hasattr(self, "fks_files") else {}
        
        if fks_ids is None :            
            fks_ids = getattr(self, "fks_ids") if hasattr(self, "fks_ids") else {}
                               
        for fks, Model in fks_json.items():
            if hasattr(self, fks):
                self_fks = getattr(self, fks)
                print (fks, ' \n---SELF_FKS : ', self_fks)
                if ( self_fks ):
                    getattr(instance, fks).clear()
                    for process in self_fks:
                        getattr(instance, fks).add (self.m2m_create_or_update(process, Model))        
        
        for m2m_file, Model in fks_files.items():
            self.handle_m2m_files( instance, m2m_file, Model)

        for fks, _ in fks_ids.items():
            if hasattr ( self, fks ) :
                self_fks = getattr(self, fks)
                getattr(instance, fks).set ( self_fks )

        self._instance_fk_file_manage(instance)

    def handle_m2m_files(self, instance, m2m_field:str, Model) -> None:
        if ( instance_m2m := getattr(instance, m2m_field, None) ) is None: return
        if m2m_field == 'spg_file_fks':
            self.handle_spg_file_fks (instance, m2m_field, Model, instance_m2m)
            return 

        if hasattr( self,  f"{m2m_field}_삭제"):
            if getattr(self, f"{m2m_field}_삭제") :
                instance_m2m.clear()
        
        if hasattr( self, f"{m2m_field}_json"):
            if (m2m_json:=  getattr(self, f"{m2m_field}_json" )):
                instance_m2m.set( m2m_json )

        if hasattr ( self, m2m_field):
            if (m2m := getattr(self, m2m_field) ) :
                for file in m2m:
                    instance_m2m.add( Model.objects.create(file=file))

    def m2m_create_or_update(self, process:dict, Model) -> object:
        id = process.pop('id', -1)
        if isinstance(id, int) and id >0:
            Model.objects.filter(id = id).update(**process)
            return Model.objects.get(id=id)
        else :
            return  Model.objects.create(**process)
        

    def handle_spg_file_fks (self, instance, m2m_field, Model, instance_m2m):
        """ only 2개인 파일을 순서대로 update하기 위해 """
        print ('handel내: ', m2m_field, getattr(self, f"{m2m_field}_json" ) )

        if hasattr( self,  f"{m2m_field}_삭제"):
            if getattr(self, f"{m2m_field}_삭제") :
                instance_m2m.clear()

        ids = []
        if hasattr ( self, m2m_field):
            if (m2m := getattr(self, m2m_field) ) :
                for file in m2m:
                    ids.append( Model.objects.create(file=file) ) 
        
        if hasattr( self, f"{m2m_field}_json"):
            if (m2m_json:=  getattr(self, f"{m2m_field}_json" )):
                if all ( id == -1 for id in m2m_json) :
                    instance_m2m.set(ids)
                else :
                    instance_m2m.clear()
                    for id in m2m_json:
                        if id == -1 and ids:
                            instance_m2m.add(ids.pop(0))
                        elif id >0 :
                            instance_m2m.add(id)
        else:
            if ids:
                instance_m2m.set(ids)
