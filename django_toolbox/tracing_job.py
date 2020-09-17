import elasticapm
from rq.job import Job


class TracingJob(Job):
    def perform(self):
        client = elasticapm.Client()
        client.begin_transaction("backgroundjob")
        context = {"args": self.args, "kwargs": self.kwargs}
        elasticapm.set_custom_context(context)
        try:
            super().perform()
            client.end_transaction(self.func_name, "success")
        except:
            client.capture_exception()
            client.end_transaction(self.func_name, "failure")
            raise
        finally:
            client.close()
