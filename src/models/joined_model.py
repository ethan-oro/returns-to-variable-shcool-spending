import sys, os
sys.path.append('./../data_processing/')
from dataprocess import *
from sklearn import linear_model
from sklearn import svm
NUM_TRIALS = 1000

def main():
	data = grab_data_full()
	joint_model = JoinedModel(len(data['intermediate'].keys()), regularization1 = False, regularization2 = True)
	avg1, avg2, names, avg_train_scores, avg_test_scores = multiple_splits(joint_model, data)
	print('xxxx')
	print(avg1)
	print(avg2)
	for i in range(len(names)):
		print names[i]
		print avg_train_scores[i]
		print avg_test_scores[i]


def multiple_splits(model, data, noisy = False):
	sum_score_train = 0
	sum_score_test = 0
	sum_train_scores = 0
	sum_test_scores = 0
	for i in range(NUM_TRIALS):
		score_train, score_test, names, train_scores, test_scores = model.train(data)
		sum_score_train += score_train
		sum_score_test += score_test
		sum_train_scores += train_scores
		sum_test_scores += test_scores

	avg_score_train = sum_score_train / NUM_TRIALS
	avg_score_test = sum_score_test / NUM_TRIALS
	avg_train_scores = sum_train_scores / NUM_TRIALS
	avg_test_scores = sum_test_scores / NUM_TRIALS

	return avg_score_train, avg_score_test, names, avg_train_scores, avg_test_scores

class JoinedModel(object):
	def __init__(self, num_inputs, type1 = "linear_regression", type2 = "linear_regression", regularization1 = False, regularization2 = False):
		if type1 == "linear_regression":
			if regularization1:
				self.models1 = [linear_model.Ridge() for i in range(num_inputs)]
			else:
				self.models1 = [linear_model.LinearRegression(normalize=False) for i in range(num_inputs)]
		elif type == "SVM":
			self.models1 = [svm.SVR() for i in range(num_inputs)]

		if type2 == "linear_regression":
			if regularization2:
				self.model2 = linear_model.Ridge()
			else:
				self.model2 = linear_model.LinearRegression(normalize=True)
		elif type2 == "SVM":
			self.model2 = svm.SVR()

	def _transform_data(self, dataframe_x, dataframe_intermediate, dataframe_y, train_split = 0.8):
		m,n = dataframe_x.shape

		x = np.array(dataframe_x)
		y = np.array(dataframe_y)
		z = np.array(dataframe_intermediate)
		random_state = np.random.get_state()
		np.random.shuffle(x)
		np.random.set_state(random_state)
		np.random.shuffle(y)
		np.random.set_state(random_state)
		np.random.shuffle(z)
		split_ind = int(train_split*m)

		x_train = x[:split_ind,:]
		y_train = y[:split_ind]
		z_train = z[:split_ind,:]

		x_test = x[split_ind:,:]
		y_test = y[split_ind:]
		z_test = z[split_ind:,:]

		means = np.nanmean(x_train, axis=0)
		x_train = np.nan_to_num(x_train)
		x_test = np.nan_to_num(x_test)

		bad_inds_train = np.where(x_train == 0)
		bad_inds_test = np.where(x_test == 0)

		x_train[bad_inds_train] = np.take(means, bad_inds_train[1])
		x_test[bad_inds_test] = np.take(means, bad_inds_test[1])

		means = np.nanmean(z_train, axis=0)
		z_train = np.nan_to_num(z_train)
		z_test = np.nan_to_num(z_test)

		bad_inds_train = np.where(z_train == 0)
		bad_inds_test = np.where(z_test == 0)

		z_train[bad_inds_train] = np.take(means, bad_inds_train[1])
		z_test[bad_inds_test] = np.take(means, bad_inds_test[1])

		return (x_train, z_train, y_train, x_test, z_test, y_test)

	def train(self, data, data_key = 'highschool', noisy = False):
		# data_key is one of 'full', 'highschool', 'middleschool', 'elementary'
		data_always_x = data['%s_always_x'%data_key]
		data_intermediate = data['%s_intermediate'%data_key]
		data_second_y = data['%s_second_y'%data_key]
		self.always_x_train, self.intermediate_train, self.y_train, self.always_x_test, self.intermediate_test, self.y_test = self._transform_data(data_always_x, data_intermediate, data_second_y)

		train_scores = np.zeros(len(data_intermediate.keys()))

		train_intermediate_predictions = []
		for i in range(len(data_intermediate.keys())):
			model = self.models1[i]
			key = data_intermediate.keys()[i]
			model.fit(self.always_x_train, self.intermediate_train.T[i].T)
			train_intermediate_predictions.append(model.predict(self.always_x_train))
			train_scores[i] += model.score(self.always_x_train, self.intermediate_train.T[i].T)

		train_intermediate = np.array(train_intermediate_predictions)
		self.model2.fit(np.concatenate((self.always_x_train, self.intermediate_train), axis = 1), self.y_train)
		score1 = self.model2.score(np.concatenate((self.always_x_train, train_intermediate.T), axis = 1), self.y_train)

		test_scores = np.zeros(len(data_intermediate.keys()))
		test_intermediate_predictions = []
		for i in range(len(data_intermediate.keys())):
			model = self.models1[i]
			key = data_intermediate.keys()[i]
			test_intermediate_predictions.append(model.predict(self.always_x_test))
			test_scores[i] = model.score(self.always_x_test, self.intermediate_test.T[i].T)

		test_intermediate = np.array(test_intermediate_predictions)
		score2 = self.model2.score(np.concatenate((self.always_x_test, test_intermediate.T), axis = 1), self.y_test)

		return score1, score2, data_intermediate.keys(), train_scores, test_scores



if __name__ == '__main__':
	main()
