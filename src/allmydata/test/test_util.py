
def foo(): pass # keep the line number constant

import os
from twisted.trial import unittest
from twisted.internet import defer, reactor
from twisted.python import failure

from allmydata.util import base32, idlib, humanreadable, mathutil, hashutil
from allmydata.util import assertutil, fileutil, testutil, deferredutil
from allmydata.util import limiter

class Base32(unittest.TestCase):
    def test_b2a_matches_Pythons(self):
        import base64
        y = "\x12\x34\x45\x67\x89\x0a\xbc\xde\xf0"
        x = base64.b32encode(y)
        while x and x[-1] == '=':
            x = x[:-1]
        x = x.lower()
        self.failUnlessEqual(base32.b2a(y), x)
    def test_b2a(self):
        self.failUnlessEqual(base32.b2a("\x12\x34"), "ci2a")
    def test_b2a_or_none(self):
        self.failUnlessEqual(base32.b2a_or_none(None), None)
        self.failUnlessEqual(base32.b2a_or_none("\x12\x34"), "ci2a")
    def test_a2b(self):
        self.failUnlessEqual(base32.a2b("ci2a"), "\x12\x34")
        self.failUnlessRaises(AssertionError, base32.a2b, "b0gus")

class IDLib(unittest.TestCase):
    def test_nodeid_b2a(self):
        self.failUnlessEqual(idlib.nodeid_b2a("\x00"*20), "a"*32)

class NoArgumentException(Exception):
    def __init__(self):
        pass

class HumanReadable(unittest.TestCase):
    def test_repr(self):
        hr = humanreadable.hr
        self.failUnlessEqual(hr(foo), "<foo() at test_util.py:2>")
        self.failUnlessEqual(hr(self.test_repr),
                             "<bound method HumanReadable.test_repr of <allmydata.test.test_util.HumanReadable testMethod=test_repr>>")
        self.failUnlessEqual(hr(1L), "1")
        self.failUnlessEqual(hr(10**40),
                             "100000000000000000...000000000000000000")
        self.failUnlessEqual(hr(self), "<allmydata.test.test_util.HumanReadable testMethod=test_repr>")
        self.failUnlessEqual(hr([1,2]), "[1, 2]")
        self.failUnlessEqual(hr({1:2}), "{1:2}")
        try:
            raise RuntimeError
        except Exception, e:
            self.failUnless(
                hr(e) == "<RuntimeError: ()>" # python-2.4
                or hr(e) == "RuntimeError()") # python-2.5
        try:
            raise RuntimeError("oops")
        except Exception, e:
            self.failUnless(
                hr(e) == "<RuntimeError: 'oops'>" # python-2.4
                or hr(e) == "RuntimeError('oops',)") # python-2.5
        try:
            raise NoArgumentException
        except Exception, e:
            self.failUnless(
                hr(e) == "<NoArgumentException>" # python-2.4
                or hr(e) == "NoArgumentException()") # python-2.5


class MyList(list):
    pass

class Math(unittest.TestCase):
    def test_div_ceil(self):
        f = mathutil.div_ceil
        self.failUnlessEqual(f(0, 1), 0)
        self.failUnlessEqual(f(0, 2), 0)
        self.failUnlessEqual(f(0, 3), 0)
        self.failUnlessEqual(f(1, 3), 1)
        self.failUnlessEqual(f(2, 3), 1)
        self.failUnlessEqual(f(3, 3), 1)
        self.failUnlessEqual(f(4, 3), 2)
        self.failUnlessEqual(f(5, 3), 2)
        self.failUnlessEqual(f(6, 3), 2)
        self.failUnlessEqual(f(7, 3), 3)

    def test_next_multiple(self):
        f = mathutil.next_multiple
        self.failUnlessEqual(f(5, 1), 5)
        self.failUnlessEqual(f(5, 2), 6)
        self.failUnlessEqual(f(5, 3), 6)
        self.failUnlessEqual(f(5, 4), 8)
        self.failUnlessEqual(f(5, 5), 5)
        self.failUnlessEqual(f(5, 6), 6)
        self.failUnlessEqual(f(32, 1), 32)
        self.failUnlessEqual(f(32, 2), 32)
        self.failUnlessEqual(f(32, 3), 33)
        self.failUnlessEqual(f(32, 4), 32)
        self.failUnlessEqual(f(32, 5), 35)
        self.failUnlessEqual(f(32, 6), 36)
        self.failUnlessEqual(f(32, 7), 35)
        self.failUnlessEqual(f(32, 8), 32)
        self.failUnlessEqual(f(32, 9), 36)
        self.failUnlessEqual(f(32, 10), 40)
        self.failUnlessEqual(f(32, 11), 33)
        self.failUnlessEqual(f(32, 12), 36)
        self.failUnlessEqual(f(32, 13), 39)
        self.failUnlessEqual(f(32, 14), 42)
        self.failUnlessEqual(f(32, 15), 45)
        self.failUnlessEqual(f(32, 16), 32)
        self.failUnlessEqual(f(32, 17), 34)
        self.failUnlessEqual(f(32, 18), 36)
        self.failUnlessEqual(f(32, 589), 589)

    def test_pad_size(self):
        f = mathutil.pad_size
        self.failUnlessEqual(f(0, 4), 0)
        self.failUnlessEqual(f(1, 4), 3)
        self.failUnlessEqual(f(2, 4), 2)
        self.failUnlessEqual(f(3, 4), 1)
        self.failUnlessEqual(f(4, 4), 0)
        self.failUnlessEqual(f(5, 4), 3)

    def test_is_power_of_k(self):
        f = mathutil.is_power_of_k
        for i in range(1, 100):
            if i in (1, 2, 4, 8, 16, 32, 64):
                self.failUnless(f(i, 2), "but %d *is* a power of 2" % i)
            else:
                self.failIf(f(i, 2), "but %d is *not* a power of 2" % i)
        for i in range(1, 100):
            if i in (1, 3, 9, 27, 81):
                self.failUnless(f(i, 3), "but %d *is* a power of 3" % i)
            else:
                self.failIf(f(i, 3), "but %d is *not* a power of 3" % i)

    def test_next_power_of_k(self):
        f = mathutil.next_power_of_k
        self.failUnlessEqual(f(0,2), 1)
        self.failUnlessEqual(f(1,2), 1)
        self.failUnlessEqual(f(2,2), 2)
        self.failUnlessEqual(f(3,2), 4)
        self.failUnlessEqual(f(4,2), 4)
        for i in range(5, 8): self.failUnlessEqual(f(i,2), 8, "%d" % i)
        for i in range(9, 16): self.failUnlessEqual(f(i,2), 16, "%d" % i)
        for i in range(17, 32): self.failUnlessEqual(f(i,2), 32, "%d" % i)
        for i in range(33, 64): self.failUnlessEqual(f(i,2), 64, "%d" % i)
        for i in range(65, 100): self.failUnlessEqual(f(i,2), 128, "%d" % i)

        self.failUnlessEqual(f(0,3), 1)
        self.failUnlessEqual(f(1,3), 1)
        self.failUnlessEqual(f(2,3), 3)
        self.failUnlessEqual(f(3,3), 3)
        for i in range(4, 9): self.failUnlessEqual(f(i,3), 9, "%d" % i)
        for i in range(10, 27): self.failUnlessEqual(f(i,3), 27, "%d" % i)
        for i in range(28, 81): self.failUnlessEqual(f(i,3), 81, "%d" % i)
        for i in range(82, 200): self.failUnlessEqual(f(i,3), 243, "%d" % i)

    def test_ave(self):
        f = mathutil.ave
        self.failUnlessEqual(f([1,2,3]), 2)
        self.failUnlessEqual(f([0,0,0,4]), 1)
        self.failUnlessAlmostEqual(f([0.0, 1.0, 1.0]), .666666666666)


class Asserts(unittest.TestCase):
    def should_assert(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except AssertionError, e:
            return str(e)
        except Exception, e:
            self.fail("assert failed with non-AssertionError: %s" % e)
        self.fail("assert was not caught")

    def should_not_assert(self, func, *args, **kwargs):
        if "re" in kwargs:
            regexp = kwargs["re"]
            del kwargs["re"]
        try:
            func(*args, **kwargs)
        except AssertionError, e:
            self.fail("assertion fired when it should not have: %s" % e)
        except Exception, e:
            self.fail("assertion (which shouldn't have failed) failed with non-AssertionError: %s" % e)
        return # we're happy


    def test_assert(self):
        f = assertutil._assert
        self.should_assert(f)
        self.should_assert(f, False)
        self.should_not_assert(f, True)

        m = self.should_assert(f, False, "message")
        self.failUnlessEqual(m, "'message' <type 'str'>", m)
        m = self.should_assert(f, False, "message1", othermsg=12)
        self.failUnlessEqual("'message1' <type 'str'>, othermsg: 12 <type 'int'>", m)
        m = self.should_assert(f, False, othermsg="message2")
        self.failUnlessEqual("othermsg: 'message2' <type 'str'>", m)

    def test_precondition(self):
        f = assertutil.precondition
        self.should_assert(f)
        self.should_assert(f, False)
        self.should_not_assert(f, True)

        m = self.should_assert(f, False, "message")
        self.failUnlessEqual("precondition: 'message' <type 'str'>", m)
        m = self.should_assert(f, False, "message1", othermsg=12)
        self.failUnlessEqual("precondition: 'message1' <type 'str'>, othermsg: 12 <type 'int'>", m)
        m = self.should_assert(f, False, othermsg="message2")
        self.failUnlessEqual("precondition: othermsg: 'message2' <type 'str'>", m)

    def test_postcondition(self):
        f = assertutil.postcondition
        self.should_assert(f)
        self.should_assert(f, False)
        self.should_not_assert(f, True)

        m = self.should_assert(f, False, "message")
        self.failUnlessEqual("postcondition: 'message' <type 'str'>", m)
        m = self.should_assert(f, False, "message1", othermsg=12)
        self.failUnlessEqual("postcondition: 'message1' <type 'str'>, othermsg: 12 <type 'int'>", m)
        m = self.should_assert(f, False, othermsg="message2")
        self.failUnlessEqual("postcondition: othermsg: 'message2' <type 'str'>", m)

class FileUtil(unittest.TestCase):
    def mkdir(self, basedir, path, mode=0777):
        fn = os.path.join(basedir, path)
        fileutil.make_dirs(fn, mode)

    def touch(self, basedir, path, mode=None, data="touch\n"):
        fn = os.path.join(basedir, path)
        f = open(fn, "w")
        f.write(data)
        f.close()
        if mode is not None:
            os.chmod(fn, mode)

    def test_rm_dir(self):
        basedir = "util/FileUtil/test_rm_dir"
        fileutil.make_dirs(basedir)
        # create it again to test idempotency
        fileutil.make_dirs(basedir)
        d = os.path.join(basedir, "doomed")
        self.mkdir(d, "a/b")
        self.touch(d, "a/b/1.txt")
        self.touch(d, "a/b/2.txt", 0444)
        self.touch(d, "a/b/3.txt", 0)
        self.mkdir(d, "a/c")
        self.touch(d, "a/c/1.txt")
        self.touch(d, "a/c/2.txt", 0444)
        self.touch(d, "a/c/3.txt", 0)
        os.chmod(os.path.join(d, "a/c"), 0444)
        self.mkdir(d, "a/d")
        self.touch(d, "a/d/1.txt")
        self.touch(d, "a/d/2.txt", 0444)
        self.touch(d, "a/d/3.txt", 0)
        os.chmod(os.path.join(d, "a/d"), 0)

        fileutil.rm_dir(d)
        self.failIf(os.path.exists(d))
        # remove it again to test idempotency
        fileutil.rm_dir(d)

    def test_remove_if_possible(self):
        basedir = "util/FileUtil/test_remove_if_possible"
        fileutil.make_dirs(basedir)
        self.touch(basedir, "here")
        fn = os.path.join(basedir, "here")
        fileutil.remove_if_possible(fn)
        self.failIf(os.path.exists(fn))
        fileutil.remove_if_possible(fn) # should be idempotent
        fileutil.rm_dir(basedir)
        fileutil.remove_if_possible(fn) # should survive errors

    def test_open_or_create(self):
        basedir = "util/FileUtil/test_open_or_create"
        fileutil.make_dirs(basedir)
        fn = os.path.join(basedir, "here")
        f = fileutil.open_or_create(fn)
        f.write("stuff.")
        f.close()
        f = fileutil.open_or_create(fn)
        f.seek(0, 2)
        f.write("more.")
        f.close()
        f = open(fn, "r")
        data = f.read()
        f.close()
        self.failUnlessEqual(data, "stuff.more.")

    def test_NamedTemporaryDirectory(self):
        basedir = "util/FileUtil/test_NamedTemporaryDirectory"
        fileutil.make_dirs(basedir)
        td = fileutil.NamedTemporaryDirectory(dir=basedir)
        name = td.name
        self.failUnless(basedir in name)
        self.failUnless(basedir in repr(td))
        self.failUnless(os.path.isdir(name))
        del td
        # it is conceivable that we need to force gc here, but I'm not sure
        self.failIf(os.path.isdir(name))

    def test_rename(self):
        basedir = "util/FileUtil/test_rename"
        fileutil.make_dirs(basedir)
        self.touch(basedir, "here")
        fn = os.path.join(basedir, "here")
        fn2 = os.path.join(basedir, "there")
        fileutil.rename(fn, fn2)
        self.failIf(os.path.exists(fn))
        self.failUnless(os.path.exists(fn2))

    def test_du(self):
        basedir = "util/FileUtil/test_du"
        fileutil.make_dirs(basedir)
        d = os.path.join(basedir, "space-consuming")
        self.mkdir(d, "a/b")
        self.touch(d, "a/b/1.txt", data="a"*10)
        self.touch(d, "a/b/2.txt", data="b"*11)
        self.mkdir(d, "a/c")
        self.touch(d, "a/c/1.txt", data="c"*12)
        self.touch(d, "a/c/2.txt", data="d"*13)

        used = fileutil.du(basedir)
        self.failUnlessEqual(10+11+12+13, used)

class PollMixinTests(unittest.TestCase):
    def setUp(self):
        self.pm = testutil.PollMixin()

    def test_PollMixin_True(self):
        d = self.pm.poll(check_f=lambda : True,
                         pollinterval=0.1)
        return d

    def test_PollMixin_False_then_True(self):
        i = iter([False, True])
        d = self.pm.poll(check_f=i.next,
                         pollinterval=0.1)
        return d

    def test_timeout(self):
        d = self.pm.poll(check_f=lambda: False,
                         pollinterval=0.01,
                         timeout=1)
        def _suc(res):
            self.fail("poll should have failed, not returned %s" % (res,))
        def _err(f):
            f.trap(testutil.TimeoutError)
            return None # success
        d.addCallbacks(_suc, _err)
        return d

class DeferredUtilTests(unittest.TestCase):
    def test_success(self):
        d1, d2 = defer.Deferred(), defer.Deferred()
        good = []
        bad = []
        dlss = deferredutil.DeferredListShouldSucceed([d1,d2])
        dlss.addCallbacks(good.append, bad.append)
        d1.callback(1)
        d2.callback(2)
        self.failUnlessEqual(good, [[1,2]])
        self.failUnlessEqual(bad, [])

    def test_failure(self):
        d1, d2 = defer.Deferred(), defer.Deferred()
        good = []
        bad = []
        dlss = deferredutil.DeferredListShouldSucceed([d1,d2])
        dlss.addCallbacks(good.append, bad.append)
        d1.addErrback(lambda _ignore: None)
        d2.addErrback(lambda _ignore: None)
        d1.callback(1)
        d2.errback(RuntimeError())
        self.failUnlessEqual(good, [])
        self.failUnlessEqual(len(bad), 1)
        f = bad[0]
        self.failUnless(isinstance(f, failure.Failure))
        self.failUnless(f.check(RuntimeError))

class HashUtilTests(unittest.TestCase):

    def test_random_key(self):
        k = hashutil.random_key()
        self.failUnlessEqual(len(k), hashutil.KEYLEN)

    def test_sha256d(self):
        h1 = hashutil.tagged_hash("tag1", "value")
        h2 = hashutil.tagged_hasher("tag1")
        h2.update("value")
        h2a = h2.digest()
        h2b = h2.digest()
        self.failUnlessEqual(h1, h2a)
        self.failUnlessEqual(h2a, h2b)

    def test_sha256d_truncated(self):
        h1 = hashutil.tagged_hash("tag1", "value", 16)
        h2 = hashutil.tagged_hasher("tag1", 16)
        h2.update("value")
        h2 = h2.digest()
        self.failUnlessEqual(len(h1), 16)
        self.failUnlessEqual(len(h2), 16)
        self.failUnlessEqual(h1, h2)

    def test_chk(self):
        h1 = hashutil.convergence_hash(3, 10, 1000, "data", "secret")
        h2 = hashutil.convergence_hasher(3, 10, 1000, "secret")
        h2.update("data")
        h2 = h2.digest()
        self.failUnlessEqual(h1, h2)

    def test_hashers(self):
        h1 = hashutil.block_hash("foo")
        h2 = hashutil.block_hasher()
        h2.update("foo")
        self.failUnlessEqual(h1, h2.digest())

        h1 = hashutil.uri_extension_hash("foo")
        h2 = hashutil.uri_extension_hasher()
        h2.update("foo")
        self.failUnlessEqual(h1, h2.digest())

        h1 = hashutil.plaintext_hash("foo")
        h2 = hashutil.plaintext_hasher()
        h2.update("foo")
        self.failUnlessEqual(h1, h2.digest())

        h1 = hashutil.crypttext_hash("foo")
        h2 = hashutil.crypttext_hasher()
        h2.update("foo")
        self.failUnlessEqual(h1, h2.digest())

        h1 = hashutil.crypttext_segment_hash("foo")
        h2 = hashutil.crypttext_segment_hasher()
        h2.update("foo")
        self.failUnlessEqual(h1, h2.digest())

        h1 = hashutil.plaintext_segment_hash("foo")
        h2 = hashutil.plaintext_segment_hasher()
        h2.update("foo")
        self.failUnlessEqual(h1, h2.digest())

class Limiter(unittest.TestCase):
    def job(self, i, foo):
        self.calls.append( (i, foo) )
        self.simultaneous += 1
        self.peak_simultaneous = max(self.simultaneous, self.peak_simultaneous)
        d = defer.Deferred()
        def _done():
            self.simultaneous -= 1
            d.callback("done")
        reactor.callLater(1.0, _done)
        return d

    def bad_job(self, i, foo):
        raise RuntimeError("bad_job %d" % i)

    def test_limiter(self):
        self.calls = []
        self.simultaneous = 0
        self.peak_simultaneous = 0
        l = limiter.ConcurrencyLimiter()
        dl = []
        for i in range(20):
            dl.append(l.add(self.job, i, foo=str(i)))
        d = defer.DeferredList(dl, fireOnOneErrback=True)
        def _done(res):
            self.failUnlessEqual(self.simultaneous, 0)
            self.failUnless(self.peak_simultaneous <= 10)
            self.failUnlessEqual(len(self.calls), 20)
            for i in range(20):
                self.failUnless( (i, str(i)) in self.calls)
        d.addCallback(_done)
        return d

    def test_errors(self):
        self.calls = []
        self.simultaneous = 0
        self.peak_simultaneous = 0
        l = limiter.ConcurrencyLimiter()
        dl = []
        for i in range(20):
            dl.append(l.add(self.job, i, foo=str(i)))
        d2 = l.add(self.bad_job, 21, "21")
        d = defer.DeferredList(dl, fireOnOneErrback=True)
        def _most_done(res):
            self.failUnless(self.peak_simultaneous <= 10)
            self.failUnlessEqual(len(self.calls), 20)
            for i in range(20):
                self.failUnless( (i, str(i)) in self.calls)
            def _good(res):
                self.fail("should have failed, not got %s" % (res,))
            def _err(f):
                f.trap(RuntimeError)
                self.failUnless("bad_job 21" in str(f))
            d2.addCallbacks(_good, _err)
            return d2
        d.addCallback(_most_done)
        def _all_done(res):
            self.failUnlessEqual(self.simultaneous, 0)
            self.failUnless(self.peak_simultaneous <= 10)
            self.failUnlessEqual(len(self.calls), 20)
            for i in range(20):
                self.failUnless( (i, str(i)) in self.calls)
        d.addCallback(_all_done)
        return d
