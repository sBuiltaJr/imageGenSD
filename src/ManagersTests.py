#Defines all unit tests for the files under the /managers folder.  This file
#must be defiend at a Package level that encapsulates all includes for the
#utilities Pacakges.

#####  Imports  #####

from . import MockClasses as mc
from .db import MariadbIfc as mdb
from .managers import DailyEventMgr as dem
from .managers import QueueMgr as qm
from .utilities import JobFactory as jf
from .utilities import NameRandomizer as nr
import discord as dis
import json
import multiprocessing as mp
import pathlib as pl
import queue
import time
from typing import Callable, Optional, Any
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock


#####  Daily Event Manager Class  #####

class TestDailyEventManager(unittest.TestCase):

    def setUp(self):
        """Method called to prepare the test fixture. This is called
           immediately before calling the test method; other than
           AssertionError or SkipTest, any exception raised by this method will
           be considered an error rather than a test failure. The default
           implementation does nothing.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        #This section is intentionally written like the actual code in
        #imageGenSD.py.
        cfg_path  = pl.Path('src/config/config.json')

        with open(cfg_path.absolute()) as json_file:
            params = json.load(json_file)

        self.options   = params['daily_opts']
        mdb.MariadbIfc = mc.MockDbInterface()

        self.uut = dem.DailyEventManager(opts=self.options)

    def testStartWorks(self):
        """A simple verification that the Daily Event task can be correctly
           started.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.uut.start()
        self.assertTrue(True)

    def testDailyRollReseWorks(self):
        """A simple verification that the DailyRollRese task runs up to calling
           the DB interface.
           Note: a quick of the current implementation requires throwing an
                 exception to exit the 'while True' loop in the function.
           TODO: update function to fix the above.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        time.sleep = MagicMock()
        self.uut.dailyRollReset()
        self.assertTrue(True)

#####  Queue Manager Class  #####

class TestQueueManager(unittest.TestCase):

    def setUp(self):
        """Method called to prepare the test fixture. This is called
           immediately before calling the test method; other than
           AssertionError or SkipTest, any exception raised by this method will
           be considered an error rather than a test failure. The default
           implementation does nothing.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        #This section is intentionally written like the actual code in
        #imageGenSD.py.
        cfg_path = pl.Path('src/config/config.json')

        with open(cfg_path.absolute()) as json_file:
            params = json.load(json_file)

        self.options = params['queue_opts']

        self.uut = qm.Manager(manager_id = 1,
                              opts=self.options)

        self.metadata = {'ctx'     : mc.MockInteraction(),
                         'db_ifc'  : mc.MockDbInterface(),
                         'loop'    : mc.MockLoop(),
                         'post_fn' : mc.post,
                         'tag_rng' : mc.MockTagSource()
        }

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        self.job = jf.JobFactory.getJob(type=jf.JobTypeEnum.TESTGET,
                                        ctx=self.metadata['ctx'])

    def testQueueManagerBuilds(self):
        """A simple verification that the Queue Manager class will build
           correctly if given valid inputs.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.assertTrue(True)

    def testFlushSetsFlush(self):
        """Verifies that the Flush function correctly sets the 'flush' flag

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        self.uut.flush()

        self.assertTrue(self.uut.flush)

    def testAddAcceptsValidInput(self):
        """Verifies that the add function behaves correctly with valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.job.randomize = True

        result = self.uut.add(metadata=self.metadata,
                              job=self.job)
        qm.jobs = {}

        self.assertEqual(result, "Your job was added to the queue.  Please wait for it to finish before posting another.")

    def testAddRejectsExcessiveGuildCount(self):
        """Verifies that the add function rejects adding jobs if it is already
           serving the maximum number of Guilds.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        for x in range (self.uut.max_guilds + 1):
            qm.jobs[x] = x
        result = self.uut.add(metadata=self.metadata,
                              job=self.job)
        qm.jobs = {}

        self.assertEqual(result, "Bot is currently servicing the maximum number of allowed Guilds.")

    def testAddRejectsExcessiveJobCount(self):
        """Verifies that the add function rejects adding jobs if it is already
           at the job limit for a Guild.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.uut.max_guild_reqs = 0

        result = self.uut.add(metadata=self.metadata,
                              job=self.job)
        qm.jobs = {}

        self.assertEqual(result, "Unable to add your job, too many jobs from this Guild are already in the queue.")

    def testAddRejectsDuplicateJobs(self):
        """Verifies that the add function rejects adding jobs if it is already
           has a job from that user in the queue (per guild).

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        qm.jobs[mc.DEFAULT_GUILD_ID] = {}

        result = self.uut.add(metadata=self.metadata,
                              job=self.job)

        self.assertEqual(result, "Your job was added to the queue.  Please wait for it to finish before posting another.")

        result = self.uut.add(metadata=self.metadata,
                              job=self.job)
        qm.jobs = {}

        self.assertEqual(result, "You already have a job on the queue, please wait until it's finished.")

    #def testAddThrowsExceptionWhenFull(self):
        """Verifies that the add function rejects adding jobs if it is already
           alraedy full.

           Input: self - Pointer to the current object instance.

           Output: none.
        """


        #self.uut.queue = mp.Queue(1)

        #result = self.uut.add(metadata=self.metadata,
        #                      job=self.job)

        #self.assertEqual(result, "Your job was added to the queue.  Please wait for it to finish before posting another.")

        #with self.assertRaises(queue.Full):

        #    self.job.user_id = 1

        #    result = self.uut.add(metadata=self.metadata,
        #                          job=self.job)
        #qm.jobs = {}

    #def testPutJobMainPathWorks(self):
        """Verifies that the putJob function runs correctly with valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        #self.uut.flush_queue         = True
        #self.uut.job_cooldown        = 0.01
        #qm.jobs[mc.DEFAULT_GUILD_ID] = {}
        #qm.jobs[mc.DEFAULT_GUILD_ID][mc.DEFAULT_PROFILE_ID] = self.metadata
        #self.uut.queue.put(self.job)

        #mp.Queue = MagicMock(spec=mc.MockQueue)
        #result = self.uut.add(metadata=self.metadata,
        #                      job=self.job)

        #self.assertEqual(result, "Your job was added to the queue.  Please wait for it to finish before posting another.")

        #with patch('multiprocessing.Queue') as mc.MockQueue :
        #self.uut.putJob()
        #qm.jobs = {}

        #self.assertTrue(self.uut.flush)
