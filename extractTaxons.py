#! /usr/bin/python3
#-*-conding:utf-8-*-
import sys, re
import pickle


lstRelations=[]
idsSourcesTaxons = []
idsTargetsTaxons = []
introductorsConceptsIds = []

#dictConceptTaxons : dictionnaire
#cle = cle = idConcept
# valeur : liste = [string, list1,list2,list3,list4,list5]
#	string : nom concept
#	list1 : liste de l'extension simplifie
#	list2 : liste de l'intention simplifie
#	list3 : liste de toute l'extension du concept, meme herite
#	list4 : liste de toute l'intension du concept, meme herite
#	list5 : tout les successeurs(cibles) du concept
#	list6 : tout les predesseurs (sources) du concept
dictConceptTaxons = {} 
dictConceptTraits = {} 

outputFile = "TaxonRules.txt"
output = open(outputFile,'w')


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
	lstAttrRel = []
	for attr in lstIntension:
		for relation in lstRelations:			
			expAttRel = '(.*)'+relation+'(.*)'
			res = re.search(expAttRel,attr)
			if res:
				quantifier = res.group(1)
				conceptName = res.group(2)
				RelationnalAttribut = quantifier+' '+relation+conceptName
				lstAttrRel.append(RelationnalAttribut)
			
	
	return lstAttrRel

def getConcepts(formalcontextName,dictionnaire):
	expression = '(\d+) \[.*\{Concept\_'+formalcontextName+'\_(\d+).*'
	for line in content:	
		res = re.search(expression,line)	
		if res : 
			conceptId = res.group(1)
			conceptName = 'Concept_'+formalcontextName+'_'+res.group(2)
			lst = line.split('|')

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
				if (source not in idsSourcesTaxons):
					idsSourcesTaxons.append(source)
				if (target not in idsTargetsTaxons):
					idsTargetsTaxons.append(target)		
        		#ajouter la cible a la liste des successeurs du concept "source"
        			

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

						 	
def interpreteTrait(lstAttrRel,dictConceptTraits):
	lstTraitsInterprete = []
	expression = '.*Concept\_traits\_(\d+)[)]'	
	for attrRel in lstAttrRel:
		res = re.search(expression,attrRel)
		if res:			
			conceptTraitName = "Concept_traits_"+res.group(1)
			for idConceptTraits in dictConceptTraits:
				if dictConceptTraits[idConceptTraits][0]==conceptTraitName:
					lstTraitsInterprete = lstTraitsInterprete+dictConceptTraits[idConceptTraits][1]

	return lstTraitsInterprete 			

def writeInFile(sourceConceptName,sourceLstAttrRel,support,successorConceptName,successorLstAttrRel):
	if support!=0:

		premisse = ','.join(interpreteTrait(sourceLstAttrRel,dictConceptTraits))
		conclusion = ','.join(interpreteTrait(successorLstAttrRel,dictConceptTraits))

		output.write(sourceConceptName+str(sourceLstAttrRel)+" -> "+successorConceptName+str(successorLstAttrRel)+"\n\n")
		output.write(premisse+" -> "+conclusion+"\n")
		output.write("support = "+str(support)+"\n")
		output.write("------------------------------------------------------\n")
		output.write("------------------------------------------------------\n")


def extractRules(content,formalContextTaxonsName,formalContextTraitsName,lstRelations):
#Debut Programme
	
	getConcepts(formalContextTaxonsName,dictConceptTaxons) #parametre taxons
	getSuccessorsPredecessors(dictConceptTaxons)
	getIntroductorsConcept(dictConceptTaxons)
	getIdSourceIdTarget(dictConceptTaxons)

	getConcepts(formalContextTraitsName,dictConceptTraits) #parametre traits

	print("introductor concepts taxons number : "+str(len(introductorsConceptsIds)))



	for idConcept in dictConceptTaxons.keys():
		getAllExtension(idConcept,dictConceptTaxons)
		getAllIntension(idConcept,dictConceptTaxons)



	#extraction de regles
	for sourceConceptId in introductorsConceptsIds:
		sourceConceptName = dictConceptTaxons[sourceConceptId][0]
		sourceLstAttrRel = dictConceptTaxons[sourceConceptId][2]
		support = len(dictConceptTaxons[sourceConceptId][3])

		for successorID in dictConceptTaxons[sourceConceptId][5]:
			if successorID in introductorsConceptsIds:
				successorConceptName = dictConceptTaxons[successorID][0]
				successorLstAttrRel = dictConceptTaxons[successorID][2]
				#write in Output File
				writeInFile(sourceConceptName,sourceLstAttrRel,support,successorConceptName,successorLstAttrRel)
			else:
				while successorID not in introductorsConceptsIds:
					if (successorID in idsTargetsTaxons) and (successorID not in idsSourcesTaxons):
						break
					else:
						newSource = successorID
						for successor in dictConceptTaxons[newSource][5]:
							successorID = successor
							if successorID in introductorsConceptsIds:
								successorConceptName = dictConceptTaxons[successorID][0]
								successorLstAttrRel = dictConceptTaxons[successorID][2]
								#write in Output File
								writeInFile(sourceConceptName,sourceLstAttrRel,support,successorConceptName,successorLstAttrRel)				 	
#print(len(introductorsConceptsIds))
#print(introductorsConceptsIds)
#for cle in dictConceptTaxons.keys():
#	print(cle,':',dictConceptTaxons[cle][4])

	inputFile.close()
	output.close()
	print("taxons rules extraction complete.")


if __name__ == '__main__':
	if len(sys.argv) < 5:
		print('script must have at least 5 parameters')
		sys.exit(1)
	else:
		fileName = sys.argv[1]
		inputFile = open(fileName)
		content = inputFile.readlines()

		formalContextTaxonsName = sys.argv[2]
		formalContextTraitsName = sys.argv[3]
		i=4
		while i<len(sys.argv):
			lstRelations.append(sys.argv[i])
			i=i+1

		
		extractRules(content,formalContextTaxonsName,formalContextTraitsName,lstRelations)	
		
		#serialiser les variables 
		## dictConceptTaxons, dictConceptTraits, introductorsConceptsIds
		#pour les utiliser dans le fichier extractionStations.py
		pickle.dump(dictConceptTaxons, open( "saveDictConceptTaxons.p", "wb" ) )
		pickle.dump(dictConceptTraits, open( "saveDictConceptTraits.p", "wb" ) )		
		pickle.dump(introductorsConceptsIds, open( "saveIntroductorsConceptsIds.p", "wb" ) )
