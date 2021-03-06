"""
author: robert.knobloch@stud.tu-darmstadt.de

Program managing the operational data storage (MongoDB) of the DPT.
PyMongo docs: https://pymongo.readthedocs.io/en/stable/
"""

from pymongo import MongoClient
from bson.objectid import ObjectId
import time


from dpt_module import DptModule, Requests, Responses

class OpData(DptModule):
    """
    Class for interfacing with the Operational Data Storage
    """
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client["dpt_op_data"]

        super().__init__("op_data")

        self.listen()

    def listen(self) -> None:
        """
        Loop for listening to incoming requests.
        Expects a tuple with the first entry being the request type.
        """

        while True:

            col_waypoints = self.db["waypoints"]
            (sender, msg) = self.receive()

            if msg[0] == Requests.SHUTDOWN:
                break

            if msg[0] == Requests.NEW_WP:
                post = {"coordinates": msg[1],
                        "wp_name": "New WP",
                        "creation_time": time.time()}
                hash_id = col_waypoints.insert_one(post).inserted_id

            elif msg[0] == Requests.GET_WP:
                hash_id = ObjectId(msg[1])
                wp_doc = col_waypoints.find_one(hash_id)
                if wp_doc is None:
                    self.transmit(sender, (str(hash_id), Responses.NONEXISTENT_WAYPOINT))

                wp_coor = wp_doc["coordinates"]
                wp_name = wp_doc["wp_name"]
                wp_time = wp_doc["creation_time"]
                self.transmit(sender, (str(hash_id), wp_name, wp_coor, wp_time))

            elif msg[0] == Requests.GET_ALL_WP_IDS:
                all_wps_cursor = col_waypoints.find({})
                wp_all_ids = [str(wp["_id"]) for wp in all_wps_cursor]
                all_wps_cursor = col_waypoints.find({})
                wp_all_names = [wp["wp_name"] for wp in all_wps_cursor]
                self.transmit(sender, (wp_all_ids, wp_all_names))

            elif msg[0] == Requests.DEL_WP:
                hash_id = ObjectId(msg[1])
                result = col_waypoints.delete_one({"_id": hash_id})
                if result.acknowledged and result.deleted_count == 1:
                    self.transmit(sender, Requests.DEL_WP)
                else:
                    self.transmit(sender, Responses.UNEXPECTED_FAILURE)

            elif msg[0] == Requests.CHANGE_WP_NAME:
                hash_id = ObjectId(msg[1])
                new_value = {"$set": {"wp_name": msg[2]}}
                result = col_waypoints.update_one({"_id": hash_id}, new_value)
                if result.acknowledged and result.modified_count == 1:
                    self.transmit(sender, Requests.CHANGE_WP_NAME)
                else:
                    self.transmit(sender, Responses.UNEXPECTED_FAILURE)




