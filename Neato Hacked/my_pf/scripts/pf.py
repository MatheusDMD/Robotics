#!/usr/bin/env python

""" This is the starter code for the robot localization project

    Originally cloned from Paul Ruvolo's CompRobo 15:
    https://github.com/paulruvolo/comprobo15/

"""

import rospy

from std_msgs.msg import Header, String
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, PoseArray, Pose, Point, Quaternion
from nav_msgs.srv import GetMap
from copy import deepcopy

import tf
from tf import TransformListener
from tf import TransformBroadcaster
from tf.transformations import euler_from_quaternion, rotation_matrix, quaternion_from_matrix
from random import gauss

import math
import time
from scipy.stats import norm
import numpy as np
from numpy.random import random_sample
from sklearn.neighbors import NearestNeighbors
from occupancy_field import OccupancyField

from helper_functions import (convert_pose_inverse_transform,
                              convert_translation_rotation_to_pose,
                              convert_pose_to_xy_and_theta,
                              angle_diff, sum_vectors)

class Particle(object):
    """ Represents a hypothesis (particle) of the robot's pose consisting of x,y and theta (yaw)
        Attributes:
            x: the x-coordinate of the hypothesis relative to the map frame
            y: the y-coordinate of the hypothesis relative ot the map frame
            theta: the yaw of the hypothesis relative to the map frame
            w: the particle weight (the class does not ensure that particle weights are normalized
    """

    def __init__(self,x=0.0,y=0.0,theta=0.0,w=1.0):
        """ Construct a new Particle
            x: the x-coordinate of the hypothesis relative to the map frame
            y: the y-coordinate of the hypothesis relative ot the map frame
            theta: the yaw of the hypothesis relative to the map frame
            w: the particle weight (the class does not ensure that particle weights are normalized """
        self.w = w
        self.theta = theta
        self.x = x
        self.y = y

    def as_pose(self):
        """ A helper function to convert a particle to a geometry_msgs/Pose message """
        orientation_tuple = tf.transformations.quaternion_from_euler(0,0,self.theta)
        return Pose(position=Point(x=self.x,y=self.y,z=0), orientation=Quaternion(x=orientation_tuple[0], y=orientation_tuple[1], z=orientation_tuple[2], w=orientation_tuple[3]))

    # TODO: define additional helper functions if needed

class ParticleFilter:
    """ The class that represents a Particle Filter ROS Node
        Attributes list:
            initialized: a Boolean flag to communicate to other class methods that initializaiton is complete
            base_frame: the name of the robot base coordinate frame (should be "base_link" for most robots)
            map_frame: the name of the map coordinate frame (should be "map" in most cases)
            odom_frame: the name of the odometry coordinate frame (should be "odom" in most cases)
            scan_topic: the name of the scan topic to listen to (should be "scan" in most cases)
            n_particles: the number of particles in the filter
            d_thresh: the amount of linear movement before triggering a filter update
            a_thresh: the amount of angular movement before triggering a filter update
            laser_max_distance: the maximum distance to an obstacle we should use in a likelihood calculation
            pose_listener: a subscriber that listens for new approximate pose estimates (i.e. generated through the rviz GUI)
            particle_pub: a publisher for the particle cloud
            laser_subscriber: listens for new scan data on topic self.scan_topic
            tf_listener: listener for coordinate transforms
            tf_broadcaster: broadcaster for coordinate transforms
            particle_cloud: a list of particles representing a probability distribution over robot poses
            current_odom_xy_theta: the pose of the robot in the odometry frame when the last filter update was performed.
                                   The pose is expressed as a list [x,y,theta] (where theta is the yaw)
            map: the map we will be localizing ourselves in.  The map should be of type nav_msgs/OccupancyGrid
    """
    xy_theta = []

    def __init__(self):
        self.initialized = False        # make sure we don't perform updates before everything is setup
        rospy.init_node('pf')           # tell roscore that we are creating a new node named "pf"

        self.base_frame = "base_link"   # the frame of the robot base
        self.map_frame = "map"          # the name of the map coordinate frame
        self.odom_frame = "odom"        # the name of the odometry coordinate frame
        self.scan_topic = "scan"        # the topic where we will get laser scans from

        self.n_particles = 250         # the number of particles to use


        self.d_thresh = 0.2             # the amount of linear movement before performing an update
        self.a_thresh = math.pi/6       # the amount of angular movement before performing an update

        self.laser_max_distance = 2.0   # maximum penalty to assess in the likelihood field model

        self.model_noise_rate = 0.15
        # TODO: define additional constants if needed

        # Setup pubs and subs

        # pose_listener responds to selection of a new approximate robot location (for instance using rviz)
        self.pose_listener = rospy.Subscriber("initialpose", PoseWithCovarianceStamped, self.update_initial_pose)
        print()
        # publish the current particle cloud.  This enables viewing particles in rviz.
        self.particle_pub = rospy.Publisher("particlecloud", PoseArray, queue_size=10)

        # laser_subscriber listens for data from the lidar
        self.laser_subscriber = rospy.Subscriber(self.scan_topic, LaserScan, self.scan_received)

        # enable listening for and broadcasting coordinate transforms
        self.tf_listener = TransformListener()
        self.tf_broadcaster = TransformBroadcaster()

        self.particle_cloud = []

        self.current_odom_xy_theta = []

        # request the map from the map server, the map should be of type nav_msgs/OccupancyGrid
        # TODO: fill in the appropriate service call here.  The resultant map should be assigned be passed
        #       into the init method for OccupancyField
        rospy.wait_for_service('static_map')
        grid = rospy.ServiceProxy('static_map',GetMap)
        my_map = grid().map
        # for now we have commented out the occupancy field initialization until you can successfully fetch the map
        self.field = OccupancyField(my_map)
        self.initialized = True

    def create_initial_particle_list(self,xy_theta):
        init_particle_list = []
        n = self.n_particles
        for i in range(self.n_particles):
            w = 1.0/n
            x = gauss(xy_theta[0],0.5)
            y = gauss(xy_theta[1],0.5)
            theta = gauss(xy_theta[2],((math.pi)/2))
            particle = Particle(x,y,theta,w)
            init_particle_list.append(particle)
        print("init_particle_list")
        return init_particle_list

    def update_robot_pose(self):
        """ Update the estimate of the robot's pose given the updated particles.
            There are two logical methods for this:
                (1): compute the mean pose
                (2): compute the most likely pose (i.e. the mode of the distribution)
        """
        # first make sure that the particle weights are normalized
        self.normalize_particles()

        # TODO: assign the lastest pose into self.robot_pose as a geometry_msgs.Pose object
        # just to get started we will fix the robot's pose to always be at the origin
        x = 0
        y = 0
        theta = 0
        angles = []
        for particle in self.particle_cloud:
            x += particle.x * particle.w
            y += particle.y * particle.w
            v = [particle.w * math.cos(math.radians(particle.theta)), particle.w * math.sin(math.radians(particle.theta))]
            angles.append(v)
        theta = sum_vectors(angles)
        orientation = tf.transformations.quaternion_from_euler(0,0,theta)
        self.robot_pose = Pose(position=Point(x=x,y=y),orientation=Quaternion(x=orientation[0], y=orientation[1], z=orientation[2], w=orientation[3]))



    def update_particles_with_odom(self, msg):
        """ Update the particles using the newly given odometry pose.
            The function computes the value delta which is a tuple (x,y,theta)
            that indicates the change in position and angle between the odometry
            when the particles were last updated and the current odometry.

            msg: this is not really needed to implement this, but is here just in case.
        """
        print('update_w_odom')

        new_odom_xy_theta = convert_pose_to_xy_and_theta(self.odom_pose.pose)
        # compute the change in x,y,theta since our last update 
        if self.current_odom_xy_theta:
            old_odom_xy_theta = self.current_odom_xy_theta
            delta = (new_odom_xy_theta[0] - self.current_odom_xy_theta[0],
                     new_odom_xy_theta[1] - self.current_odom_xy_theta[1],
                     new_odom_xy_theta[2] - self.current_odom_xy_theta[2])

            self.current_odom_xy_theta = new_odom_xy_theta

            for particle in self.particle_cloud:
                parc = (math.atan2(delta[1], delta[0]) - old_odom_xy_theta[2]) % 360
                particle.x += (math.sqrt((delta[0]**2) + (delta[1]**2)))* math.cos(parc)
                particle.y += (math.sqrt((delta[0]**2) + (delta[1]**2))) * math.sin(parc)
                particle.theta += delta[2]
        else:
            
            self.current_odom_xy_theta = new_odom_xy_theta
            return
            
        #DONE
        # TODO: modify particles using delta
        # For added difficulty: Implement sample_motion_odometry (Prob Rob p 136)

    def map_calc_range(self,x,y,theta):
        """ Difficulty Level 3: implement a ray tracing likelihood model... Let me know if you are interested """
        # TODO: nothing unless you want to try this alternate likelihood model
        pass

    def resample_particles(self):
        """ Resample the particles according to the new particle weights.
            The weights stored with each particle should define the probability that a particular
            particle is selected in the resampling step.  You may want to make use of the given helper
            function draw_random_sample.
        """
        # make sure the distribution is normalized
        self.normalize_particles()
        values = np.empty(self.n_particles)
        probs = np.empty(self.n_particles)
        for i in range(len(self.particle_cloud)):
            values[i] = i
            probs[i] = self.particle_cloud[i].w
        new_random_particle = ParticleFilter.weighted_values(values,probs,self.n_particles)
        new_particles = []
        for i in new_random_particle:
            idx = int(i)
            s_p = self.particle_cloud[idx]
            new_particles.append(Particle(x=s_p.x+gauss(0,.025),y=s_p.y+gauss(0,.05),theta=s_p.theta+gauss(0,.05)))
        self.particle_cloud = new_particles
        self.normalize_particles()

    def update_particles_with_laser(self, msg):
        """ Updates the particle weights in response to the scan contained in the msg """
        print('update_w_laser')
        readings = msg.ranges
        for particle in self.particle_cloud:
            for read in range(0,len(readings),3):
                self.field.get_particle_likelyhood(particle,readings[read],self.model_noise_rate,read)

        self.normalize_particles()
        self.resample_particles()

    @staticmethod
    def weighted_values(values, probabilities, size):
        """ Return a random sample of size elements from the set values with the specified probabilities
            values: the values to sample from (numpy.ndarray)
            probabilities: the probability of selecting each element in values (numpy.ndarray)
            size: the number of samples
        """
        bins = np.add.accumulate(probabilities)
        return values[np.digitize(random_sample(size), bins)-1]

    @staticmethod
    def draw_random_sample(choices, probabilities, n):
        """ Return a random sample of n elements from the set choices with the specified probabilities
            choices: the values to sample from represented as a list
            probabilities: the probability of selecting each element in choices represented as a list
            n: the number of samples
        """
        print('draw_random_sample')
        values = np.array(range(len(choices)))
        probs = np.array(probabilities)
        bins = np.add.accumulate(probs)
        inds = values[np.digitize(random_sample(n), bins)]
        samples = []
        for i in inds:
            samples.append(deepcopy(choices[int(i)]))
        return samples

    def update_initial_pose(self, msg):
        """ Callback function to handle re-initializing the particle filter based on a pose estimate.
            These pose estimates could be generated by another ROS Node or could come from the rviz GUI """
        xy_theta = convert_pose_to_xy_and_theta(msg.pose.pose)
        self.initialize_particle_cloud(xy_theta)
        self.fix_map_to_odom_transform(msg)

    def initialize_particle_cloud(self, xy_theta=None):
        """ Initialize the particle cloud.
            Arguments
            xy_theta: a triple consisting of the mean x, y, and theta (yaw) to initialize the
                      particle cloud around.  If this input is ommitted, the odometry will be used """
        if xy_theta == None:
            xy_theta = convert_pose_to_xy_and_theta(self.odom_pose.pose)

        #self.particle_cloud = []
        # TODO create particles
        self.particle_cloud = self.create_initial_particle_list(xy_theta)

        self.normalize_particles()
        self.update_robot_pose()

    def normalize_particles(self):
        """ Make sure the particle weights define a valid distribution (i.e. sum to 1.0) """
        w_sum = sum([p.w for p in self.particle_cloud])

        for particle in self.particle_cloud:
            particle.w /= w_sum
        # TODO: implement this

    def publish_particles(self, msg):

        print('publish_particles')
        particles_conv = []
        for p in self.particle_cloud:
            particles_conv.append(p.as_pose())
        # actually send the message so that we can view it in rviz
        self.particle_pub.publish(PoseArray(header=Header(stamp=rospy.Time.now(),
                                            frame_id=self.map_frame),
                                              poses=particles_conv))

    def scan_received(self, msg):
        """ This is the default logic for what to do when processing scan data.
            Feel free to modify this, however, I hope it will provide a good
            guide.  The input msg is an object of type sensor_msgs/LaserScan """

        print('scan_received')
        if not(self.initialized):
            # wait for initialization to complete
            return

        if not(self.tf_listener.canTransform(self.base_frame,msg.header.frame_id,msg.header.stamp)):
            # need to know how to transform the laser to the base frame
            # this will be given by either Gazebo or neato_node
            return

        if not(self.tf_listener.canTransform(self.base_frame,self.odom_frame,msg.header.stamp)):
            # need to know how to transform between base and odometric frames
            # this will eventually be published by either Gazebo or neato_node
            return

        # calculate pose of laser relative ot the robot base
        p = PoseStamped(header=Header(stamp=rospy.Time(0),
                                      frame_id=msg.header.frame_id))
        self.laser_pose = self.tf_listener.transformPose(self.base_frame,p)

        # find out where the robot thinks it is based on its odometry
        p = PoseStamped(header=Header(stamp=rospy.Time(0),
                                      frame_id=self.base_frame),
                        pose=Pose())
        self.odom_pose = self.tf_listener.transformPose(self.odom_frame, p)
        # store the the odometry pose in a more convenient format (x,y,theta)
        new_odom_xy_theta = convert_pose_to_xy_and_theta(self.odom_pose.pose)

        if not(self.particle_cloud):
            # now that we have all of the necessary transforms we can update the particle cloud
            self.initialize_particle_cloud()
            # cache the last odometric pose so we can only update our particle filter if we move more than self.d_thresh or self.a_thresh
            self.current_odom_xy_theta = new_odom_xy_theta
            # update our map to odom transform now that the particles are initialized
            self.fix_map_to_odom_transform(msg)
        elif (math.fabs(new_odom_xy_theta[0] - self.current_odom_xy_theta[0]) > self.d_thresh or
              math.fabs(new_odom_xy_theta[1] - self.current_odom_xy_theta[1]) > self.d_thresh or
              math.fabs(new_odom_xy_theta[2] - self.current_odom_xy_theta[2]) > self.a_thresh):
            # we have moved far enough to do an update!
            self.update_particles_with_odom(msg)    # update based on odometry
            self.update_particles_with_laser(msg)   # update based on laser scan
            self.update_robot_pose()                # update robot's pose
            self.resample_particles()               # resample particles to focus on areas of high density
            self.fix_map_to_odom_transform(msg)     # update map to odom transform now that we have new particles
        # publish particles (so things like rviz can see them)
        self.publish_particles(msg)

    def fix_map_to_odom_transform(self, msg):
        """ This method constantly updates the offset of the map and
            odometry coordinate systems based on the latest results from
            the localizer """
        (translation, rotation) = convert_pose_inverse_transform(self.robot_pose)
        p = PoseStamped(pose=convert_translation_rotation_to_pose(translation,rotation),
                        header=Header(stamp=rospy.Time(0),frame_id=self.base_frame))
        self.odom_to_map = self.tf_listener.transformPose(self.odom_frame, p)
        (self.translation, self.rotation) = convert_pose_inverse_transform(self.odom_to_map.pose)

    def broadcast_last_transform(self):
        """ Make sure that we are always broadcasting the last map
            to odom transformation.  This is necessary so things like
            move_base can work properly. """
        if not(hasattr(self,'translation') and hasattr(self,'rotation')):
            return

        print('broadcast')
        self.tf_broadcaster.sendTransform(self.translation,
                                      self.rotation,
                                      rospy.Time.now(),
                                      self.odom_frame,
                                      self.map_frame)

        #self.tf_listener.waitForTransform('/odom','/stable_scan',rospy.Time(),rospy.Duration(.1))
        #self.tf_listener.lookupTransform('/odom','/stable_scan',rospy.Time())


if __name__ == '__main__':
    n = ParticleFilter()
    r = rospy.Rate(5)
    #tf_listener.waitForTransform("/odom", "/base_scan", rospy.Time(), rospy.Duration(4.0))
    while not(rospy.is_shutdown()):
    # in the main loop all we do is continuously broadcast the latest map to odom transform
        n.broadcast_last_transform()
        r.sleep()