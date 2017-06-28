#! /usr/bin/python3
#-*-conding:utf-8-*-
import sys, re
import pickle

lstRelations=[]
introductorsConceptsIds=[]
idsSourcesStations = []
idsTargetsStations = []


outputFile = "StationsRules.txt"
output = open(outputFile,'w')

#deserialiser les variables
# dictConceptTaxons, dictConceptTraits, introductorsConceptsIds
dictConceptTaxons = pickle.load( open( "saveDictConceptTaxons.p", "rb" ) )       
dictConceptTraits = pickle.load( open( "saveDictConceptTraits.p", "rb" ) )                
introductorsConceptsTaxonsIds = pickle.load( open( "saveIntroductorsConceptsIds.p", "rb" ) )                


#dictConceptStations : dictionnaire
#cle = cle = idConcept
# valeur : liste = [string, list1,list2,list3,list4,list5]
#	string : nom concept
#	list1 : liste de l'extension simplifie
#	list2 : liste de l'intention simplifie
#	list3 : liste de toute l'extension du concept, meme herite
#	list4 : liste de toute l'intension du concept, meme herite
#	list5 : tout les successeurs(cibles) du concept
#	list6 : tout les predesseurs (sources) du concept
dictConceptStations = {}

def getIntroductorsConceptsTaxonsNames():
	lstConceptNames=[]
	for ID in  introductorsConceptsTaxonsIds:
		lstConceptNames.append(dictConceptTaxons[ID][0])
	return lstConceptNames

def getExtension(lstExtension):
	lstExt = []
	for element in lstExtension:
		expression = '(\w+)'
		res = re.search(expression,element)
		if res:
			objet = res.group(1)
			lstExt.append(objet)
	return lstExt


def getIntentionRel(lstIntension):
	introductorsConceptsTaxonsNames = getIntroductorsConceptsTaxonsNames()
	lstAttrRel = []
	for attr in lstIntension:
		for relation in lstRelations:	
			expAttRel = '(.*)'+relation+'[\(Concept\_](.*)\)'
			res = re.search(expAttRel,attr)
			if res:
				quantifier = res.group(1)
				conceptName = res.group(2)
				RelationnalAttribut = quantifier+' '+relation+'('+conceptName+')'
				if conceptName.startswith('Concept_taxons'):
					if conceptName in introductorsConceptsTaxonsNames:
						lstAttrRel.append(RelationnalAttribut)			
				else:
					lstAttrRel.append(RelationnalAttribut)		

	return lstAttrRel


def getConcept(formalcontextName,dictionnaire):
	expression = '(\d+) \[.*\{Concept\_'+formalcontextName+'\_(\d+).*'
	for line in content:
		res = re.search(expression,line)
		if res:
			conceptId = res.group(1)			
			conceptName = 'Concept_'+formalcontextName+'_'+res.group(2)
			
			lst=line.split('|')

			lstExtension = lst[2].split("\\n")
			lstExtension=getExtension(lstExtension)
			
			lstIntension = lst[1].split("\\n")
			lstAttrRel=getIntentionRel(lstIntension)

			if conceptId not in dictionnaire.keys():
				dictionnaire[conceptId]= [conceptName,lstExtension,lstAttrRel,[],[],[],[]]


def getSuccessorsPredecessors(dictionnaire):
	for line in content:
		expression='(\d+) -> (\d+)'
		res = re.search(expression,line)
		if res : 
			source = res.group(1)
			target = res.group(2)
			if source in dictionnaire.keys():
				#ajouter target a la liste de successeurs
				dictionnaire[source][5].append(target)								
			
			if target in dictionnaire.keys():
				#ajouter la source a la liste des predecesseurs
				dictionnaire[target][6].append(source) 		


def getIntroductorsConcept(dictionnaire):
	for conceptId in dictionnaire.keys():
		#si la liste des attribut relationnel n'est pas vide 
		#alors c'est un concept introducteur
		if dictionnaire[conceptId][2]: 
			introductorsConceptsIds.append(conceptId)


def getIdSourceIdTarget(dictionnaire):
	for line in content:
		expression='(\d+) -> (\d+)'						
		res = re.search(expression,line)
		if res:
			source = res.group(1)
			target = res.group(2)
			if source in dictionnaire.keys():				
				if (source not in idsSourcesStations):
					idsSourcesStations.append(source)
				if (target not in idsTargetsStations):
					idsTargetsStations.append(target)		
    

def getAllExtension(idConcept,dictionnaire):
	dictionnaire[idConcept][3]=list(dictionnaire[idConcept][1]) 
	for predecessor in dictionnaire[idConcept][6]:
		if dictionnaire[predecessor][6]:
			getAllExtension(predecessor,dictionnaire)
		for objet in dictionnaire[predecessor][3]:
			if objet not in dictionnaire[idConcept][3]:
				dictionnaire[idConcept][3].append(objet)


def getAllIntension(idConcept,dictionnaire):
	dictionnaire[idConcept][4]=list(dictionnaire[idConcept][2])  
	for successor in dictionnaire[idConcept][5]:		
		if dictionnaire[successor][5]:
			getAllIntension(successor,dictionnaire)			
		for attribut in dictionnaire[successor][4]:			
			if attribut not in dictionnaire[idConcept][4]:
				dictionnaire[idConcept][4].append(attribut)	


def writeInFile(sourceConceptName,sourceLstAttrRel,support,successorConceptName,successorLstAttrRel):
	if support!=0:
		#premisse = ','.join(interpreteTrait(sourceLstAttrRel,dictConceptTraits))
		#conclusion = ','.join(interpreteTrait(successorLstAttrRel,dictConceptTraits))
		output.write(sourceConceptName+str(sourceLstAttrRel)+" -> "+successorConceptName+str(successorLstAttrRel)+"\n\n")
		#output.write(premisse+" -> "+conclusion+"\n")
		output.write("support = "+str(support)+"\n")
		output.write("------------------------------------------------------\n")
		output.write("------------------------------------------------------\n")

def extractRules(content,formalContextStationsName):
	getConcept(formalContextStationsName,dictConceptStations)
	getSuccessorsPredecessors(dictConceptStations)
	getIntroductorsConcept(dictConceptStations)
	getIdSourceIdTarget(dictConceptStations)

	print("introductor concepts stations number : "+str(len(introductorsConceptsIds)))
	
	for idConcept in dictConceptStations.keys():
		getAllExtension(idConcept,dictConceptStations)
		getAllIntension(idConcept,dictConceptStations)

	#extraction de regles
	for sourceConceptId in introductorsConceptsIds:
		sourceConceptName = dictConceptStations[sourceConceptId][0]
		sourceLstAttrRel = dictConceptStations[sourceConceptId][2]
		support = len(dictConceptStations[sourceConceptId][3])

		for successorID in dictConceptStations[sourceConceptId][5]:
			if successorID in introductorsConceptsIds:
				successorConceptName = dictConceptStations[successorID][0]
				successorLstAttrRel = dictConceptStations[successorID][2]
				#write in Output File
				writeInFile(sourceConceptName,sourceLstAttrRel,support,successorConceptName,successorLstAttrRel)
			
			else:
				newSource = successorID
				for successor in dictConceptStations[newSource][5]:
					successorID = successor
					if successorID in introductorsConceptsIds:
						successorConceptName = dictConceptStations[successorID][0]
						successorLstAttrRel = dictConceptStations[successorID][2]
						#write in Output File
						writeInFile(sourceConceptName,sourceLstAttrRel,support,successorConceptName,successorLstAttrRel)				 	

	inputFile.close()
	output.close()
	print("stations rules extraction complete.")

	
if __name__ == '__main__':
	if len(sys.argv) ==1:
		print('erreur de parametre')
		sys.exit(1)
	else:
		fileName = sys.argv[1]
		inputFile = open(fileName)
		content = inputFile.readlines()

		formalContextStationsName = sys.argv[2]
		
		i=3
		while i<len(sys.argv):
			lstRelations.append(sys.argv[i])
			i=i+1

			
		extractRules(content,formalContextStationsName)
		


