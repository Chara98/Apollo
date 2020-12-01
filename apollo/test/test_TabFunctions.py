import unittest
from unittest import TestCase
import dataclasses
import sys, os

sys.path.append(os.path.split(os.path.abspath(__file__))[0].rsplit("\\", 2)[0])
from apollo.app.tab_manager import ApolloTabFunctions
from apollo.test.testUtilities import TesterObjects, TestSuit_main

from PyQt5 import QtWidgets, QtGui, QtCore   

# TODO
#  Documnetation -> 1.12.2020

class Test_ApolloTabFunctions_selection(TestCase):
    """
    Class to test all the functions that get Indexes Of all the selected Items From Views and Tables
    """
    
    def setUp(self):
        """
        Initilizes the class and loads a Db in Memory
        """
        self.TabInstance = ApolloTabFunctions()
        self.TabInstance.LoadDB(":memory:")
        
    def tearDown(self):
        del self.TabInstance
        
    def test_ColumnSelection_INDEX(self):
        """
        Tests the Indexing and returing of values From inside a TBV that have been selected
        either by using index
        
        Expected Behaviour:
        Takes A TableView and Column Index or FieldName as an input and returns all the
        items that are selected in a Table.
        """
        # checks for indexing at 0 column
        (RawTable, TableView) = TesterObjects.Gen_TableView()
        TableView.selectAll()
        
        with (self.subTest("Indexing Column using Integer index")):
            ResultTable = self.TabInstance._ColumnSelection(TableView, 0)
            ExpectedTable = [row[0] for row in RawTable]
            self.assertEqual(ExpectedTable, ResultTable)
            
        with (self.subTest("Indexing Column using String Column Name")):
            field = self.TabInstance.LIB_MANG.db_fields[5]
            # checks for indexing at 0 column
            ResultTable = self.TabInstance._ColumnSelection(TableView, field)
            # index column same as the index of DB fields
            ExpectedTable = [row[5] for row in RawTable]
            self.assertEqual(ExpectedTable, ResultTable)        
        
        with (self.subTest("Indexing Column using Out Of bounds")):        
            # checks for Out of bounds indexing
            ResultTable = self.TabInstance._ColumnSelection(TableView, 1000)
            self.assertEqual(None, ResultTable)


    def test_GetSelectionIndexes(self):
        """
        Used to test Data retrival from a view of all the selected Indexes
        
        Expected Behaviour:
        Takes A TableView as an input and returns all the items that are selected in a Table.
        """
        (RawTable, TableView) = TesterObjects.Gen_TableView()
        TableView.selectAll()
        ResultTable = self.TabInstance._GetSelectionIndexes(TableView)
        self.assertEqual(RawTable, ResultTable)
        
        
class Test_ApolloTabFunctions_Queueing(TestCase):
    """
    Tests for all track queuing and table Refreshes
    """
    
    def setUp(self):
        self.TabInstance = ApolloTabFunctions()
        self.TabInstance.LoadDB(":memory:")
        self.DataTable = TesterObjects.Gen_DbTable_Data(10)
        self.TabInstance.LIB_MANG.BatchInsert_Metadata(self.DataTable)

    def tearDown(self):
        del self.TabInstance
        
    def test_PlayNow(self):
        """
        Test clearing the original queue and adding New Items to a queue
        
        Expected Behaviour:
            Clears the Queue whenever new data is added and is indexed Using File_id
        """
        NUMROWS = 10
        View = TesterObjects.Gen_TableView_fromData(self.DataTable)
        View.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        
        with (self.subTest("test adding 4 Items to an empty queue")):
            [View.selectRow(R) for R in range(4)]
            
            # Adds items to an empty queue
            self.TabInstance.PlayNow(View)            
            View.clearSelection()
            
            # gets result from DB as items dont need order
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","file_id"))
            Expected = self.DataTable["file_id"][:4] # checks with expected value
            self.assertEqual(Expected, Result)
            
            
        with (self.subTest("test readding last 4 Items to an filled queue")):
            [View.selectRow(R) for R in [6, 7, 8, 9]]
            
            # Adds new items to an filled queue
            self.TabInstance.PlayNow(View)            
            View.clearSelection()
            
            # gets result from DB as items dont need order 
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","file_id"))    
            Expected = self.DataTable["file_id"][6:]
            self.assertEqual(Expected, Result)
            
        
    def test_QueueNext(self):
        """
        Test adding New Items to a queue after the current pointer
        
        Expected Behaviour:
            Adds Data After the Pointer in the Queue whenever new data is ready and is indexed Using File_id
        """
        NUMROWS = 10
        View = TesterObjects.Gen_TableView_fromData(self.DataTable)
        View.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        
        with (self.subTest("test Queuing 4 Items to an empty queue")):
            [View.selectRow(R) for R in range(4)]
            # Adds items to an empty queue
            self.TabInstance.QueueNext(View)            
            View.clearSelection()
            
            # gets data from DataTable to check for data simmilarity
            Expected = self.DataTable["file_id"][:4]
            
            with (self.subTest("test Queuing 4 Items to an queue in DB")):
                Result = self.TabInstance.LIB_MANG.IndexSelector("nowplaying","file_id")
                self.assertEqual(Expected, Result)
                
            with (self.subTest("test Queuing 4 Items to an queue in PlayQueue")):
                Result = self.TabInstance.PlayQueue.GetQueue()
                self.assertEqual(Expected, Result)
            
        with (self.subTest("test Queuing last 6 Items to an filled queue")):
            [View.selectRow(R) for R in [4, 5, 6, 7, 8, 9]]
            # Adds items after pointer to queue
            self.TabInstance.QueueNext(View)            
            View.clearSelection()
            
            # gets data from DataTable to check for data simmilarity
            Expected = ['file_idX0', 'file_idX4', 'file_idX5', 'file_idX6', 'file_idX7',
                        'file_idX8', 'file_idX9', 'file_idX1', 'file_idX2', 'file_idX3']
            
            # order is important in which playqueue is arranged but not in Db            
            with (self.subTest("test Queuing 6 Items to an queue in DB")):
                Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","file_id"))
                [self.assertIn(val, Expected) for val in Result]
                
            with (self.subTest("test Queuing 6 Items to an queue in PlayQueue")):
                Result = self.TabInstance.PlayQueue.GetQueue()
                self.assertEqual(Expected, Result)   
    
    def test_QueueLast(self):
        """
        Test adding new items at the end of the queue
        
        Expected Behaviour:
            Adds Data at the end in the Queue whenever new data is ready and is indexed Using File_id
        """
        NUMROWS = 10
        View = TesterObjects.Gen_TableView_fromData(self.DataTable)
        View.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        
        with (self.subTest("test adding 4 Items to an empty queue")):
            [View.selectRow(R) for R in range(4)]
            # Adds items to an empty queue
            self.TabInstance.QueueLast(View)            
            View.clearSelection()
            Expected = self.DataTable["file_id"][:4]
            
            with (self.subTest("test Queuing 4 Items to an queue in DB")):
                Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","file_id"))
                self.assertEqual(Expected, Result)
            
            with (self.subTest("test Queuing 4 Items to an queue in PlayQueue")):
                Result = self.TabInstance.PlayQueue.GetQueue()
                self.assertEqual(Expected, Result)            

        with (self.subTest("test readding last 4 Items to the end of the queue")):
            [View.selectRow(R) for R in [6, 7, 8, 9]]
            # Adds items To the end of the queue
            self.TabInstance.QueueLast(View)            
            View.clearSelection()
            Expected = [v for i, v in enumerate(self.DataTable["file_id"]) if i not in [4, 5]]
            
            with (self.subTest("test Queuing 6 Items to an queue in DB")):
                Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","file_id"))
                self.assertEqual(Expected, Result)
            
            with (self.subTest("test Queuing 6 Items to an queue in PlayQueue")):
                Result = self.TabInstance.PlayQueue.GetQueue()
                self.assertEqual(Expected, Result) 
            
            
    def test_PlayAllShuffled(self):
        """
        Test adding Shuffled items in the queue and clearing the queue
        
        Expected Behaviour:
            Adds Shuffled Data in the Queue whenever new data is ready and is indexed Using File_id
        """        
        NUMROWS = 10
        View = TesterObjects.Gen_TableView_fromData(self.DataTable)
        View.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        
        with (self.subTest("test Shuffle adding 4 Items to an empty queue")):
            [View.selectRow(R) for R in range(4)]
            
            # Adds items to an empty queue
            self.TabInstance.PlayAllShuffled(View)            
            View.clearSelection()
            
            # gets result from DB as items dont need order
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","file_id"))
            Expected = self.DataTable["file_id"][:4] # checks with expected value
            [self.assertIn(val, Expected) for val in Result]
            self.assertNotEqual(Expected, Result)
            
        with (self.subTest("test shuffle readding last 4 Items to an filled queue")):
            [View.selectRow(R) for R in [6, 7, 8, 9]]
            
            # Adds new items to an filled queue
            self.TabInstance.PlayAllShuffled(View)            
            View.clearSelection()
            
            # gets result from DB as items dont need order 
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","file_id"))    
            Expected = self.DataTable["file_id"][6:]
            [self.assertIn(val, Expected) for val in Result]
            self.assertNotEqual(Expected, Result)
            
    
    def test_PlayArtist(self):
        """
        Test adding Similar Artist items in the queue and clearing the queue
        
        Expected Behaviour:
            Adds Data in the Queue whenever new data is ready and is indexed Using artist
        """         
        NUMROWS = 10
        View = TesterObjects.Gen_TableView_fromData(self.DataTable)
        View.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        
        with (self.subTest("test Shuffle adding 4 Items to an empty queue")):
            [View.selectRow(R) for R in range(4)]
            # Adds items to an empty queue
            self.TabInstance.PlayArtist(View)            
            View.clearSelection()
            # gets result from DB as items dont need order
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","artist"))
            Expected = self.DataTable["artist"][:4] # checks with expected value
            self.assertEqual(Expected, Result)

            
        with (self.subTest("test shuffle readding last 4 Items to an filled queue")):
            [View.selectRow(R) for R in [6, 7, 8, 9]]
            # Adds new items to an filled queue
            self.TabInstance.PlayArtist(View)            
            View.clearSelection()
            # gets result from DB as items dont need order 
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","artist"))    
            Expected = self.DataTable["artist"][6:]
            self.assertEqual(Expected, Result)

    
    def test_PlayAlbumNow(self):
        """
        Test adding Similar Album items in the queue and clearing the queue
        
        Expected Behaviour:
            Adds Data in the Queue whenever new data is ready and is indexed Using album
        """ 
        NUMROWS = 10
        View = TesterObjects.Gen_TableView_fromData(self.DataTable)
        View.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        
        with (self.subTest("test Shuffle adding 4 Items to an empty queue")):
            [View.selectRow(R) for R in range(4)]
            # Adds items to an empty queue
            self.TabInstance.PlayAlbumNow(View)            
            View.clearSelection()
            # gets result from DB as items dont need order
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","album"))
            Expected = self.DataTable["album"][:4] # checks with expected value
            self.assertEqual(Expected, Result)
            
        with (self.subTest("test shuffle readding last 4 Items to an filled queue")):
            [View.selectRow(R) for R in [6, 7, 8, 9]]
            # Adds new items to an filled queue
            self.TabInstance.PlayAlbumNow(View)            
            View.clearSelection()
            # gets result from DB as items dont need order 
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","album"))    
            Expected = self.DataTable["album"][6:]
            self.assertEqual(Expected, Result)
    
    def test_QueueAlbumNext(self):
        """
        Test adding Similar Album items in the queue
        
        Expected Behaviour:
            Adds Data After the Pointer in the Queue whenever new data is ready and is indexed Using album
        """
        
        # test Stetup that creates a view with selected rows 
        NUMROWS = 10
        View = TesterObjects.Gen_TableView_fromData(self.DataTable)
        View.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        [View.selectRow(R) for R in range(4)]
        self.TabInstance.PlayAlbumNow(View)
        View.clearSelection()       
            
        with (self.subTest("test Queuing last 6 Items to an filled queue")):
            [View.selectRow(R) for R in [4, 5, 6, 7, 8, 9]]
            # Adds items after pointer to queue
            self.TabInstance.QueueAlbumNext(View)            
            View.clearSelection()            

            # order is important in which playqueue is arranged but not in Db            
            with (self.subTest("test Queuing 6 Items to an queue in DB")):
                # gets data from DataTable to check for data simmilarity
                Expected = ['albumX0', 'albumX4', 'albumX5', 'albumX6', 'albumX7',
                            'albumX8', 'albumX9', 'albumX1', 'albumX2', 'albumX3']                
                Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","album"))
                [self.assertIn(val, Expected) for val in Result]
                
            with (self.subTest("test Queuing 6 Items to an queue in PlayQueue")):
                # gets data from DataTable to check for data simmilarity
                Expected = ['file_idX0', 'file_idX4', 'file_idX5', 'file_idX6', 'file_idX7',
                            'file_idX8', 'file_idX9', 'file_idX1', 'file_idX2', 'file_idX3']                
                Result = self.TabInstance.PlayQueue.GetQueue()
                self.assertEqual(Expected, Result)          
        
    
    def test_QueueAlbumLast(self):
        """
        Test adding Similar Album items in the queue
        
        Expected Behaviour:
            Adds Data in the end of the Queue whenever new data is ready and is indexed Using album
        """         
        # test Stetup that creates a view with selected rows 
        NUMROWS = 10
        View = TesterObjects.Gen_TableView_fromData(self.DataTable)
        View.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        [View.selectRow(R) for R in range(4)]
        self.TabInstance.PlayAlbumNow(View)
        View.clearSelection()       
            
        with (self.subTest("test Queuing last 6 Items to an filled queue")):
            [View.selectRow(R) for R in [4, 5, 6, 7, 8, 9]]
            # Adds items after pointer to queue
            self.TabInstance.QueueAlbumLast(View)            
            View.clearSelection()            

            # order is important in which playqueue is arranged but not in Db            
            with (self.subTest("test Queuing 6 Items to an queue in DB")):
                # gets data from DataTable to check for data simmilarity
                Expected = ['albumX0', 'albumX4', 'albumX5', 'albumX6', 'albumX7',
                            'albumX8', 'albumX9', 'albumX1', 'albumX2', 'albumX3']                
                Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","album"))
                [self.assertIn(val, Expected) for val in Result]
                
            with (self.subTest("test Queuing 6 Items to an queue in PlayQueue")):
                # gets data from DataTable to check for data simmilarity
                Expected = ['file_idX0', 'file_idX1', 'file_idX2', 'file_idX3', 'file_idX4',
                            'file_idX5', 'file_idX6', 'file_idX7','file_idX8', 'file_idX9', ]                
                Result = self.TabInstance.PlayQueue.GetQueue()
                self.assertEqual(Expected, Result)       
       
    def test_PlayGenre(self):
        """
        Test adding Similar genre items in the queue
        
        Expected Behaviour:
            Adds Data in the Queue whenever new data is ready and is indexed Using genre
        """        
        NUMROWS = 10
        View = TesterObjects.Gen_TableView_fromData(self.DataTable)
        View.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        
        with (self.subTest("test Shuffle adding 4 Items to an empty queue")):
            [View.selectRow(R) for R in range(4)]
            # Adds items to an empty queue
            self.TabInstance.PlayGenre(View)            
            View.clearSelection()
            # gets result from DB as items dont need orde
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","genre"))
            Expected = self.DataTable["genre"][:4] # checks with expected value
            self.assertEqual(Expected, Result)
            
        with (self.subTest("test shuffle readding last 4 Items to an filled queue")):
            [View.selectRow(R) for R in [6, 7, 8, 9]]
            # Adds new items to an filled queue
            self.TabInstance.PlayGenre(View)            
            View.clearSelection()
            # gets result from DB as items dont need order 
            Result = (self.TabInstance.LIB_MANG.IndexSelector("nowplaying","genre"))    
            Expected = self.DataTable["genre"][6:]
            self.assertEqual(Expected, Result)     
                       
if __name__ == "__main__":
    App = QtWidgets.QApplication([])
    Suite = TestSuit_main()
    Suite.AddTest(Test_ApolloTabFunctions_selection)
    Suite.AddTest(Test_ApolloTabFunctions_Queueing)    
    Suite.Run(True)
