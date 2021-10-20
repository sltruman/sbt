#include <iostream>
#include "TCPServer.h"
#include "main_online.cpp"
TCPServer tcp;

void * loop(void * m)
{
        pthread_detach(pthread_self());
	while(1)
	{
		std::string boxmessage = tcp.getMessage();
		std::string placementmessage = "";
		if( boxmessage != "" )
		{
			cout <<"@@@@@@@@@@@@@@@@@@@@@@@@@"<<endl;
			OnlinePacking::PlanPlacement(boxmessage,placementmessage);
			OnlinePacking::ResetPallet();
			cout <<"@@@@@@@@@@@@@@@@@@@@@@@@@"<<endl;
			tcp.Send(placementmessage);
			tcp.clean();
		}
		sleep(0.5);
	}
	tcp.detach();
}

int main()
{
	pthread_t msg;
	tcp.setup(9898);
	if( pthread_create(&msg, NULL, loop, (void *)0) == 0)
	{
		cout<<"test!"<<endl;
		tcp.receive();
		cout<<"tcp.receive:"<<tcp.receive()<<endl;
		string str = tcp.getMessage();
		cout<<"1111111"<<str<<endl;
		tcp.Send("recv ok!!!!");
		tcp.clean();
		tcp.detach();
		}
}
