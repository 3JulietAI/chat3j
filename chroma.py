from uuid import uuid4
import chromadb
from chromadb.utils import embedding_functions


class ChromaHandler:
    """
    A class to handle all interactions with the chroma database.
    """
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    chroma = chromadb.PersistentClient(path="library/chroma.db")
        

    def chroma_get_collection(self, name: str) -> chromadb.Collection:
        """
        Load a collection from the chroma database.
        """
        collection = self.chroma.get_collection(name=name)
        return collection


    def chroma_get_or_create_collection(self, name: str) -> chromadb.Collection:
        """
        Load a collection from the chroma database. If the collection does not exist, create it.

        :param name: The name of the collection to load or create.
        """
        collection = self.chroma.get_or_create_collection(name=name, embedding_function=self.embedding_function)
        
        return collection


    def chroma_delete_collection(self, name: str) -> None:
        """
        Deleta a collection from the chroma database.

        :param name: The name of the collection to delete.
        """
        self.chroma.delete_collection(name=name)
        print(f"Deleted collection: {name}")


    def chroma_upsert_to_collection(self, collection, document, metadata, id):
        """
        Add documents to a collection.

        :param collection: The collection to add documents to.
        :param documents: A list of documents to add to the collection. (["This is a document", "This is another document"])
        :param metadatas: A list of metadata to add to the collection. ([{"source": "my_source"}, {"source": "my_source"}])
        :param ids: A list of ids to add to the collection. (["id1", "id2"])
        """
        collection.upsert(ids=id,
                        metadatas=metadata, 
                        documents=document,
        )


    def chroma_collection_change_name(self, collection: str, new_name: str) -> None:
        """
        Change the name of a collection in the chroma database.

        :param collection: The collection to change the name of.
        :param new_name: The new name of the collection.
        """
        collection.change_name(name=new_name)


    def chroma_query_collection(self, collection: str, query: str, n_results: int) -> list:
        """
        Query a collection and return (n_results) nearest neighbors.

        :param collection: The collection to query.
        :param query: The query to use. ("This is a query")
        :param n_results: The number of results to return.
        returns: A list of results.
        """
        results = collection.query(query_texts=query, 
                                n_results=n_results,
        )

        return results


    def chroma_upser_agent_command(self, command_name: str, command: str) -> None:
        """
        Add a command to the agent commands collection.

        :param command_name: The name of the command to add.
        :param command: The command to add.
        """
        self.chroma_upsert_to_collection(collection=self.chroma_get_or_create_collection("agent_commands"),
                                    document=[command],
                                    metadata=[{"name": command_name}],
                                    id=[command_name],
        )


    def upsert_chunks_from_corpus(self, corpus_path: str, collection_name: str) -> None:
            """
            Upserts chunks from a corpus file into the agent's collection. kb=knowledgebase

            :param corpus_path: The path to the corpus file.
            """
            collection = self.chroma_get_or_create_collection(self.name)
            with open(corpus_path, 'r') as file:
                corpus = file.read()
            corpus_chunks = corpus.split('\n\n')
            for chunk in corpus_chunks:
                self.chroma_upsert_to_collection(collection=collection_name, metadata=None, document=chunk, id=f"{self.name}-kb-{str(uuid4())}")
            print("Corpus chunks upserted.")


    def chroma_results_format_to_prompt(self, chroma_results):
        if not chroma_results["documents"] or all(not doc for doc in chroma_results["documents"]):
            return "No results found."
        formatted_output = ""
        for result in chroma_results["documents"]:
            # Join the list into a string if the result is a list
            if isinstance(result, list):
                result = " ".join(result)

        # Split the result into components (sender, timestamp, message)
        components = result.split(" @ ")
        sender = components[0].strip()
        timestamp = components[1].strip()
        message = " @ ".join(components[2:]).strip()
        # Format each entry
        formatted_output += f"\n{sender} ({timestamp}):\n{message}"
        

        return formatted_output